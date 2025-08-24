#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "boto3>=1.34.0",
#   "click>=8.1.0",
#   "rich>=13.0.0",
# ]
# ///

"""
S3 Sync Script for GitHub Actions
Handles various file sync patterns to AWS S3 with flexible configuration.
Designed to be run with uv: `uv run s3_sync.py`
"""

import os
import sys
import zipfile
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

import boto3
import click
from rich.console import Console
from rich.table import Table
from botocore.exceptions import ClientError

console = Console()


@dataclass
class SyncConfig:
    """Configuration for S3 sync operation"""
    bucket: str
    prefix: str
    source_path: Path
    pattern: str
    sync_type: str  # 'files', 'zip', 'directory'
    exclude_patterns: List[str]
    multi_region: bool = False
    dual_deployment: bool = False
    timestamp: str = None


class S3Syncer:
    """Handles S3 sync operations with various strategies"""
    
    def __init__(self, region: str = "us-east-1"):
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region
        
    def discover_regional_buckets(self, bucket_pattern: str) -> List[Dict[str, str]]:
        """Discover regional S3 buckets based on naming pattern"""
        try:
            console.print(f"[cyan]Discovering regional buckets matching pattern: {bucket_pattern}")
            
            response = self.s3_client.list_buckets()
            regional_buckets = []
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                if bucket_pattern in bucket_name:
                    # Extract region from bucket name (assuming format: {pattern}-{region})
                    if bucket_name.startswith(bucket_pattern):
                        region_suffix = bucket_name[len(bucket_pattern):]
                        if region_suffix.startswith('-') and len(region_suffix) > 1:
                            region = region_suffix[1:]  # Remove leading dash
                            regional_buckets.append({
                                'bucket': bucket_name,
                                'region': region
                            })
                            console.print(f"  ✓ Found: {bucket_name} (region: {region})")
            
            console.print(f"[green]Discovered {len(regional_buckets)} regional buckets")
            return regional_buckets
            
        except Exception as e:
            console.print(f"[red]Error discovering regional buckets: {e}")
            return []
        
    def validate_bucket(self, bucket: str) -> bool:
        """Validate that the bucket exists and is accessible"""
        try:
            console.print(f"[cyan]Validating bucket access: {bucket}")
            
            # Check if bucket exists and we have access
            self.s3_client.head_bucket(Bucket=bucket)
            
            # Test write permissions with a small test object
            test_key = f"_test_access_{os.getpid()}"
            try:
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=test_key,
                    Body=b'test',
                    Metadata={'purpose': 'access-validation'}
                )
                
                # Clean up test object
                self.s3_client.delete_object(Bucket=bucket, Key=test_key)
                
                console.print(f"  ✓ Bucket {bucket} exists and is writable")
                return True
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDenied':
                    console.print(f"  ✗ Access denied to bucket {bucket}. Check IAM permissions.", style="red")
                else:
                    console.print(f"  ✗ Cannot write to bucket {bucket}: {e}", style="red")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket' or e.response['Error'].get('HTTPStatusCode') == 404:
                console.print(f"  ✗ Bucket {bucket} does not exist (404 Not Found)", style="red")
            elif error_code == 'AccessDenied':
                console.print(f"  ✗ Access denied to bucket {bucket}. Check IAM permissions.", style="red")
            elif error_code == 'Forbidden':
                console.print(f"  ✗ Forbidden access to bucket {bucket}. May not exist or insufficient permissions.", style="red")
            else:
                console.print(f"  ✗ Error validating bucket {bucket}: {e}", style="red")
            return False
        except Exception as e:
            error_msg = str(e)
            if "Unable to locate credentials" in error_msg:
                console.print(f"  ✗ AWS credentials not found. Configure credentials using 'aws configure' or environment variables.", style="red")
            elif "No credentials found" in error_msg or "credentials" in error_msg.lower():
                console.print(f"  ✗ AWS credentials error: {error_msg}", style="red")
            else:
                console.print(f"  ✗ Unexpected error validating bucket {bucket}: {e}", style="red")
            return False
        
    def sync_files(self, config: SyncConfig, target_bucket: str = None, target_region: str = None) -> Dict[str, int]:
        """Sync individual files to S3"""
        stats = {"uploaded": 0, "skipped": 0, "failed": 0}
        
        bucket = target_bucket or config.bucket
        region = target_region or self.region
        
        # Use specific region client if different
        s3_client = self.s3_client
        if region != self.region:
            s3_client = boto3.client('s3', region_name=region)
        
        console.print(f"[cyan]Syncing files from {config.source_path} to s3://{bucket}/{config.prefix} (region: {region})")
        
        # Find files matching pattern
        files = list(config.source_path.glob(config.pattern))
        
        for file_path in files:
            if file_path.is_file():
                # Check exclusions
                if any(pattern in str(file_path) for pattern in config.exclude_patterns):
                    stats["skipped"] += 1
                    continue
                    
                # Calculate S3 key
                relative_path = file_path.relative_to(config.source_path)
                s3_key = f"{config.prefix}/{relative_path}".replace("//", "/")
                
                try:
                    self._upload_file(file_path, bucket, s3_key, s3_client)
                    console.print(f"  ✓ Uploaded: {relative_path} → {s3_key}")
                    stats["uploaded"] += 1
                except Exception as e:
                    console.print(f"  ✗ Failed: {relative_path} - {e}", style="red")
                    stats["failed"] += 1
                    
        return stats
    
    def create_and_sync_zips(self, config: SyncConfig, target_bucket: str = None, target_region: str = None) -> Dict[str, int]:
        """Create ZIP files from directories and sync to S3"""
        stats = {"uploaded": 0, "skipped": 0, "failed": 0}
        
        bucket = target_bucket or config.bucket
        region = target_region or self.region
        
        # Use specific region client if different
        s3_client = self.s3_client
        if region != self.region:
            s3_client = boto3.client('s3', region_name=region)
        
        console.print(f"[cyan]Creating ZIPs from {config.source_path} and syncing to s3://{bucket}/{config.prefix} (region: {region})")
        
        # Find directories to zip
        if config.source_path.is_dir():
            # Get immediate subdirectories
            dirs_to_zip = [d for d in config.source_path.iterdir() if d.is_dir()]
            
            for dir_path in dirs_to_zip:
                # Skip excluded directories
                if any(pattern in dir_path.name for pattern in config.exclude_patterns):
                    stats["skipped"] += 1
                    continue
                
                zip_name = f"{dir_path.name}.zip"
                zip_path = Path(f"/tmp/{zip_name}")
                
                try:
                    # Create ZIP file
                    self._create_zip(dir_path, zip_path)
                    
                    # Upload to S3
                    s3_key = f"{config.prefix}/{zip_name}".replace("//", "/")
                    self._upload_file(zip_path, bucket, s3_key, s3_client)
                    
                    console.print(f"  ✓ Zipped & Uploaded: {dir_path.name} → {s3_key}")
                    stats["uploaded"] += 1
                    
                    # Clean up temp file
                    zip_path.unlink()
                    
                except Exception as e:
                    console.print(f"  ✗ Failed: {dir_path.name} - {e}", style="red")
                    stats["failed"] += 1
                    
        return stats
    
    def sync_directory(self, config: SyncConfig, target_bucket: str = None, target_region: str = None) -> Dict[str, int]:
        """Sync entire directory structure to S3"""
        stats = {"uploaded": 0, "skipped": 0, "failed": 0}
        
        bucket = target_bucket or config.bucket
        region = target_region or self.region
        
        # Use specific region client if different
        s3_client = self.s3_client
        if region != self.region:
            s3_client = boto3.client('s3', region_name=region)
        
        console.print(f"[cyan]Syncing directory {config.source_path} to s3://{bucket}/{config.prefix} (region: {region})")
        
        for root, dirs, files in os.walk(config.source_path):
            root_path = Path(root)
            
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in config.exclude_patterns)]
            
            for file_name in files:
                file_path = root_path / file_name
                
                # Check file pattern
                if not file_path.match(config.pattern):
                    stats["skipped"] += 1
                    continue
                
                # Calculate S3 key
                relative_path = file_path.relative_to(config.source_path)
                s3_key = f"{config.prefix}/{relative_path}".replace("//", "/")
                
                try:
                    self._upload_file(file_path, bucket, s3_key, s3_client)
                    console.print(f"  ✓ Uploaded: {relative_path}")
                    stats["uploaded"] += 1
                except Exception as e:
                    console.print(f"  ✗ Failed: {relative_path} - {e}", style="red")
                    stats["failed"] += 1
                    
        return stats
    
    def _upload_file(self, file_path: Path, bucket: str, key: str, s3_client=None):
        """Upload a single file to S3"""
        client = s3_client or self.s3_client
        with open(file_path, 'rb') as f:
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType=self._get_content_type(file_path)
            )
    
    def _create_zip(self, source_dir: Path, output_path: Path):
        """Create a ZIP file from a directory"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    def _get_content_type(self, file_path: Path) -> str:
        """Determine content type based on file extension"""
        ext_map = {
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.json': 'application/json',
            '.py': 'text/x-python',
            '.sh': 'text/x-shellscript',
            '.zip': 'application/zip',
            '.json': 'application/json',
        }
        return ext_map.get(file_path.suffix, 'application/octet-stream')
    
    def sync_multi_region(self, config: SyncConfig, bucket_pattern: str) -> Dict[str, Dict[str, int]]:
        """Sync to multiple regions based on bucket discovery"""
        regional_buckets = self.discover_regional_buckets(bucket_pattern)
        
        if not regional_buckets:
            console.print(f"[yellow]No regional buckets found for pattern: {bucket_pattern}")
            return {}
        
        results = {}
        
        for bucket_info in regional_buckets:
            bucket_name = bucket_info['bucket']
            region = bucket_info['region']
            
            console.print(f"\n[bold blue]Syncing to region: {region}[/bold blue]")
            
            try:
                if config.sync_type == 'files':
                    stats = self.sync_files(config, bucket_name, region)
                elif config.sync_type == 'zip':
                    stats = self.create_and_sync_zips(config, bucket_name, region)
                elif config.sync_type == 'directory':
                    stats = self.sync_directory(config, bucket_name, region)
                else:
                    console.print(f"[red]Unknown sync type: {config.sync_type}")
                    continue
                
                results[region] = stats
                
            except Exception as e:
                console.print(f"[red]Failed to sync to {region}: {e}")
                results[region] = {"uploaded": 0, "skipped": 0, "failed": 1}
        
        return results
    
    def sync_with_dual_deployment(self, config: SyncConfig, bucket_pattern: str = None) -> Dict[str, any]:
        """Sync with both timestamp and latest paths"""
        results = {"timestamp": {}, "latest": {}}
        
        # First sync with timestamp path
        if config.multi_region and bucket_pattern:
            results["timestamp"] = self.sync_multi_region(config, bucket_pattern)
        else:
            if config.sync_type == 'files':
                results["timestamp"][self.region] = self.sync_files(config)
            elif config.sync_type == 'zip':
                results["timestamp"][self.region] = self.create_and_sync_zips(config)
            elif config.sync_type == 'directory':
                results["timestamp"][self.region] = self.sync_directory(config)
        
        # Then sync with latest path if dual deployment enabled
        if config.dual_deployment:
            console.print("\n[bold yellow]Syncing to 'latest' path[/bold yellow]")
            
            # Create config for latest path
            latest_config = SyncConfig(
                bucket=config.bucket,
                prefix=config.prefix.replace(config.timestamp, 'latest') if config.timestamp else f"{config.prefix}/latest",
                source_path=config.source_path,
                pattern=config.pattern,
                sync_type=config.sync_type,
                exclude_patterns=config.exclude_patterns,
                multi_region=config.multi_region,
                dual_deployment=False,  # Prevent infinite recursion
                timestamp=None
            )
            
            if config.multi_region and bucket_pattern:
                results["latest"] = self.sync_multi_region(latest_config, bucket_pattern)
            else:
                if config.sync_type == 'files':
                    results["latest"][self.region] = self.sync_files(latest_config)
                elif config.sync_type == 'zip':
                    results["latest"][self.region] = self.create_and_sync_zips(latest_config)
                elif config.sync_type == 'directory':
                    results["latest"][self.region] = self.sync_directory(latest_config)
        
        return results


@click.command()
@click.option('--bucket', envvar='S3_BUCKET', required=True, help='S3 bucket name')
@click.option('--prefix', envvar='S3_PREFIX', default='', help='S3 key prefix')
@click.option('--source', envvar='SOURCE_PATH', default='.', help='Source path for files')
@click.option('--pattern', envvar='FILE_PATTERN', default='*', help='File pattern to match')
@click.option('--sync-type', envvar='SYNC_TYPE', 
              type=click.Choice(['files', 'zip', 'directory']), 
              default='files',
              help='Type of sync operation')
@click.option('--exclude', envvar='EXCLUDE_PATTERNS', default='', 
              help='Comma-separated patterns to exclude')
@click.option('--region', envvar='AWS_REGION', default='us-east-1', help='AWS region')
@click.option('--dry-run', is_flag=True, help='Show what would be synced without uploading')
@click.option('--multi-region', envvar='MULTI_REGION', is_flag=True, help='Deploy to multiple regions based on bucket pattern')
@click.option('--bucket-pattern', envvar='BUCKET_PATTERN', help='Base bucket pattern for multi-region discovery (e.g., "cyngular-onboarding")')
@click.option('--dual-deployment', envvar='DUAL_DEPLOYMENT', is_flag=True, help='Deploy to both timestamp and latest paths')
@click.option('--timestamp', envvar='TIMESTAMP', help='Timestamp for versioned deployment')
def main(bucket: str, prefix: str, source: str, pattern: str, 
         sync_type: str, exclude: str, region: str, dry_run: bool,
         multi_region: bool, bucket_pattern: str, dual_deployment: bool, timestamp: str):
    """
    S3 Sync Tool - Flexible file synchronization to AWS S3
    
    Examples:
        # Sync CloudFormation templates
        S3_BUCKET=my-bucket S3_PREFIX=cfn SOURCE_PATH=./CFN FILE_PATTERN="*.yaml" uv run s3_sync.py
        
        # Create ZIPs from Lambda directories
        S3_BUCKET=my-bucket S3_PREFIX=lambdas SOURCE_PATH=./Lambdas/Services SYNC_TYPE=zip uv run s3_sync.py
        
        # Sync entire directory
        S3_BUCKET=my-bucket S3_PREFIX=project SOURCE_PATH=. SYNC_TYPE=directory FILE_PATTERN="*.py" uv run s3_sync.py
        
        # Multi-region deployment with dual paths
        BUCKET_PATTERN=cyngular-onboarding MULTI_REGION=true DUAL_DEPLOYMENT=true TIMESTAMP=20240101-120000 uv run s3_sync.py
    """
    
    # Parse exclude patterns
    exclude_patterns = [p.strip() for p in exclude.split(',') if p.strip()] if exclude else []
    
    # Create configuration
    config = SyncConfig(
        bucket=bucket,
        prefix=prefix.strip('/'),  # Remove leading/trailing slashes
        source_path=Path(source).resolve(),
        pattern=pattern,
        sync_type=sync_type,
        exclude_patterns=exclude_patterns,
        multi_region=multi_region,
        dual_deployment=dual_deployment,
        timestamp=timestamp
    )
    
    # Validate source path
    if not config.source_path.exists():
        console.print(f"[red]Error: Source path {config.source_path} does not exist")
        sys.exit(1)
    
    # Display configuration
    console.print("\n[bold]S3 Sync Configuration:[/bold]")
    table = Table(show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Bucket", config.bucket)
    table.add_row("Prefix", config.prefix or "(root)")
    table.add_row("Source", str(config.source_path))
    table.add_row("Pattern", config.pattern)
    table.add_row("Sync Type", config.sync_type)
    table.add_row("Excludes", ', '.join(config.exclude_patterns) or "(none)")
    table.add_row("Region", region)
    table.add_row("Multi-Region", str(multi_region))
    table.add_row("Bucket Pattern", bucket_pattern or "(single bucket)")
    table.add_row("Dual Deployment", str(dual_deployment))
    table.add_row("Timestamp", timestamp or "(none)")
    table.add_row("Dry Run", str(dry_run))
    
    console.print(table)
    console.print()
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be uploaded[/yellow]\n")
        return
    
    # Initialize syncer
    syncer = S3Syncer(region=region)
    
    # Validate bucket access before proceeding
    if not syncer.validate_bucket(config.bucket):
        console.print(f"[red]Bucket validation failed for {config.bucket}")
        sys.exit(1)
    console.print()
    
    # Execute sync based on type and options
    try:
        if multi_region and not bucket_pattern:
            console.print(f"[red]Error: --bucket-pattern required for multi-region deployment")
            sys.exit(1)
        
        if dual_deployment or multi_region:
            # Use enhanced sync with dual deployment and/or multi-region
            results = syncer.sync_with_dual_deployment(config, bucket_pattern)
            
            # Calculate combined stats
            stats = {"uploaded": 0, "skipped": 0, "failed": 0}
            for deployment_type, regions in results.items():
                console.print(f"\n[bold]Results for {deployment_type}:[/bold]")
                for region, region_stats in regions.items():
                    console.print(f"  {region}: {region_stats}")
                    for key in stats:
                        stats[key] += region_stats.get(key, 0)
        else:
            # Single region, single deployment
            if config.sync_type == 'files':
                stats = syncer.sync_files(config)
            elif config.sync_type == 'zip':
                stats = syncer.create_and_sync_zips(config)
            elif config.sync_type == 'directory':
                stats = syncer.sync_directory(config)
            else:
                console.print(f"[red]Unknown sync type: {config.sync_type}")
                sys.exit(1)
            
        # Display summary
        console.print("\n[bold]Sync Summary:[/bold]")
        summary_table = Table()
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green")
        
        summary_table.add_row("Uploaded", str(stats["uploaded"]))
        summary_table.add_row("Skipped", str(stats["skipped"]))
        summary_table.add_row("Failed", str(stats["failed"]))
        
        console.print(summary_table)
        
        # Exit with error if any failures
        if stats["failed"] > 0:
            sys.exit(1)
            
    except ClientError as e:
        console.print(f"[red]AWS Error: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()