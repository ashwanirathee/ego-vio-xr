from src.euroc.args import parse_args
from src.euroc.project import Project

def main(argv=None):
    """
    Main function to run the pipeline.
    """
    args = parse_args(argv)
    project = Project(args)
    project.run()


if __name__ == "__main__":
    main()