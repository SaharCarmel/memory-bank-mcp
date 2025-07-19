from daytona import Daytona
import os

def main():
    daytona = Daytona()
    sandbox = daytona.create()

    try:
        root_dir = sandbox.get_sandbox_root_dir()
        project_dir = os.path.join(root_dir, "learn-typescript")

        # Clone the repository
        sandbox.git.clone(
            "https://github.com/panaverse/learn-typescript", 
            project_dir, 
            "master"
        )

        # Pull latest changes
        sandbox.git.pull(project_dir)

    except Exception as error:
        print("Error creating sandbox:", error)
    finally:
        # Cleanup
        daytona.remove(sandbox)
