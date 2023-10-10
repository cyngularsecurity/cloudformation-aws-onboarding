import paramiko
import subprocess

def populate_dot_env():
    replacements = {
        '{{DB_HOST}}': 'db.example.com',
        '{{DB_USER}}': 'username',
        '{{DB_PASS}}': 'password'
    }

    # Read .env.example content
    with open('.env.example', 'r') as example_file:
        example_content = example_file.read()

    # Replace placeholders with actual values
    env_content = example_content
    for placeholder, value in replacements.items():
        env_content = env_content.replace(placeholder, value)

    # Write populated content to .env file
    with open('.env', 'w') as env_file:
        env_file.write(env_content)

    print('.env file populated and saved.')
    
def run_ssh_command(hostname, username, key_filename, bash_script):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, key_filename=key_filename)

        print(f"Connected to {hostname}")
        
        # Run the Bash script remotely
        stdin, stdout, stderr = ssh.exec_command(f"bash -s", get_pty=True)
        stdin.write(bash_script)
        stdin.flush()

        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            print(f"Error on {hostname}:\n{error}")
        else:
            print(f"Output from {hostname}:\n{output}")

    except Exception as e:
        print(f"Error connecting to {hostname}: {e}")
    finally:
        ssh.close()
    
def main():
    
    servers = ["server1.example.com", "server2.example.com"]  # Add your server list here
    ssh_key_path = "/path/to/your/ssh/key"  # Update with your SSH private key path
    bash_script_path = "/path/to/your/script.sh"  # Update with your Bash script path
    ssh_username = "your-ssh-user"  # Update with your SSH username

    # Read the Bash script content
    with open(bash_script_path, "r") as script_file:
        bash_script = script_file.read().encode()

    for server in servers:
        run_ssh_command(server, ssh_username, ssh_key_path, bash_script)


if __name__ == '__main__':
    main()    