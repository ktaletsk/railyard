"""Console script for railyard."""
import sys
import click
import railyard.railyard as ry

@click.group()
def main():
    """Welcome to Railyard: modular container builder."""
    pass

@main.command()
@click.argument('base_stack', nargs=1)
@click.argument('additional_stacks', nargs=-1)
def build(base_stack, additional_stacks):
    print(f'Base stack: {base_stack}')
    print(f'Additional stacks: {additional_stacks}')
    ry.test(base_stack, additional_stacks)

@main.command()
@click.argument('base_stack', nargs=1)
@click.argument('additional_stacks', nargs=-1)
@click.argument('path', nargs=1)
def assemble(base_stack, additional_stacks, path):
    print(f'Base stack: {base_stack}')
    print(f'Additional stacks: {additional_stacks}')
    print(f'Path: {path}')
    ry.assemble(base_stack, additional_stacks, path)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
