package main

import (
	"fmt"
	"io"
	"log"
	"path/filepath"

	"gopkg.in/src-d/go-git.v4"
	"gopkg.in/src-d/go-git.v4/plumbing"
	"gopkg.in/src-d/go-git.v4/plumbing/object"

	"archive/tar"
	"compress/gzip"
	"os"
)

func GzipRepo() {

	filePath := "/path/to/local/repo.tar.gz"
	Dir := "/path/to/local"
	// Create the tar.gz archive
	output, err := os.Create(filePath)
	if err != nil {
		panic(err)
	}
	defer output.Close()

	gzWriter := gzip.NewWriter(output)
	tarWriter := tar.NewWriter(gzWriter)

	// Walk through your repo files and add them to the archive
	AddToArchive(tarWriter, filePath, Dir)

	tarWriter.Close()
	gzWriter.Close()
}

func GitCloneTo() {

	pathToRepo := "/path/to/local/repo"
	repoUrl := "https://github.com/your-username/your-repo.git"
	// Clone the repository
	r, err := git.PlainClone(pathToRepo, false, &git.CloneOptions{
		URL: repoUrl,
	})
	if err != nil {
		panic(err)
	}

	UseR(r)

	// You can use the 'r' variable to access the cloned repository
	// For example, print the repository's URL
	fmt.Printf("Cloned repository URL: %s\n", r.Config().URLs[0])

	// Open the cloned repository
	repo, err := git.PlainOpen(pathToRepo)
	if err != nil {
		log.Fatalf("Failed to open repository: %v", err)
	}

	// Get the HEAD reference
	ref, err := repo.Head()
	if err != nil {
		log.Fatalf("Failed to get HEAD reference: %v", err)
	}

	// Get the commit object
	commit, err := repo.CommitObject(ref.Hash())
	if err != nil {
		log.Fatalf("Failed to get commit object: %v", err)
	}

	fmt.Printf("Commit ID: %s\n", commit.ID())
	fmt.Printf("Author: %s\n", commit.Author)
	fmt.Printf("Committer: %s\n", commit.Committer)
	fmt.Printf("Message: %s\n", commit.Message)

	// List files in the latest commit
	commitTree, err := commit.Tree()
	if err != nil {
		log.Fatalf("Failed to get commit tree: %v", err)
	}

	commitTree.Files().ForEach(func(f *object.File) error {
		fmt.Printf("File: %s\n", f.Name)
		return nil
	})
}

func AddToArchive(tw *tar.Writer, filePath, baseDir string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	info, err := file.Stat()
	if err != nil {
		return err
	}

	header, err := tar.FileInfoHeader(info, info.Name())
	if err != nil {
		return err
	}

	// Calculate the relative path within the repository
	relPath, err := filepath.Rel(baseDir, filePath)
	if err != nil {
		return err
	}
	header.Name = relPath

	if err := tw.WriteHeader(header); err != nil {
		return err
	}

	if _, err := io.Copy(tw, file); err != nil {
		return err
	}

	return nil
}

func PhaseTwo() {
	repoPath := "/path/to/local/repo"
	outputPath := "/path/to/local/repo.tar.gz"

	// Create the tar.gz archive
	output, err := os.Create(outputPath)
	if err != nil {
		log.Fatalf("Failed to create archive: %v", err)
	}
	defer output.Close()

	gzWriter := gzip.NewWriter(output)
	defer gzWriter.Close()

	tarWriter := tar.NewWriter(gzWriter)
	defer tarWriter.Close()

	err = filepath.Walk(repoPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Exclude directories
		if !info.IsDir() {
			err := AddToArchive(tarWriter, path, repoPath)
			if err != nil {
				log.Printf("Failed to add file to archive: %v", err)
			}
		}

		return nil
	})

	if err != nil {
		log.Fatalf("Error walking through repository: %v", err)
	}

	log.Println("Archive created successfully!")
}

func UseR(r *git.Repository) {
	// 	Fetching Updates:

	// Fetch updates from the remote repository:

	err := r.Fetch(&git.FetchOptions{
		RemoteName: "origin",
	})
	if err != nil {
		log.Fatalf("Failed to fetch updates: %v", err)
	}
	// Creating a New Branch:

	// Create a new branch based on an existing reference:

	newBranchRef := plumbing.NewReferenceFromStrings("refs/heads/new-branch", "refs/heads/master")
	newBranchRefHash := plumbing.NewHashReference(newBranchRef, ref.Hash())
	err := r.Storer.SetReference(newBranchRefHash)
	if err != nil {
		log.Fatalf("Failed to create new branch: %v", err)
	}
	// Checking Out a Branch:

	// Check out an existing branch:

	worktree, err := r.Worktree()
	if err != nil {
		log.Fatalf("Failed to get worktree: %v", err)
	}
	err = worktree.Checkout(&git.CheckoutOptions{
		Branch: plumbing.ReferenceName("refs/heads/other-branch"),
	})
	if err != nil {
		log.Fatalf("Failed to checkout branch: %v", err)
	}
	// Committing Changes:

	// Stage, commit, and push changes to the repository:

	worktree, err := r.Worktree()
	if err != nil {
		log.Fatalf("Failed to get worktree: %v", err)
	}
	_, err = worktree.Add(".")
	if err != nil {
		log.Fatalf("Failed to stage changes: %v", err)
	}
	commit, err := worktree.Commit("New commit", &git.CommitOptions{
		Author: &object.Signature{
			Name:  "Your Name",
			Email: "your@email.com",
		},
	})
	if err != nil {
		log.Fatalf("Failed to commit changes: %v", err)
	}
	err = r.Push(&git.PushOptions{
		RemoteName: "origin",
	})
	if err != nil {
		log.Fatalf("Failed to push changes: %v", err)
	}
}
