<h1 align="center">fichub-cli-metadata</h1>

A metadata plugin for fetching Metadata from the Fichub API for [fichub-cli](https://github.com/FicHub/fichub-cli/)<br><br>

To report issues upstream for the supported sites, visit https://fichub.net/#contact<br>

To report issues for the plugin, open an issue at https://github.com/fichub-cli-contrib/fichub-cli-metadata/issues<br>

To report issues for the CLI, open an issue at https://github.com/FicHub/fichub-cli/issues<br>

# Installation

## Using pip (Recommended)

```
pip install -U fichub-cli-metadata
```

## From Source (Might have bugs, for testing only)

```
pip install git+https://github.com/fichub-cli-contrib/fichub-cli-metadata@main
```

# Usage

```
> fichub_cli metadata
Usage: fichub_cli metadata [OPTIONS] COMMAND [ARGS]...

  A metadata plugin for fetching Metadata from the Fichub API for the fichub-cli

Options:
  -i, --input TEXT          Input: Either an URL or path to a file
  -o,  --out-dir TEXT       Path to the Output directory for files (default: Current Directory)
  -d,  --debug              Show the log in the console for debugging
  --log / --no-log          Save the logfile for debugging  [default: no-log]
  --version / --no-version  Display version & quit  [default: no-version]
  --help                    Show this message and exit.
```

### Default Configuration

- The fanfiction will be downloaded in the current directory. To change it, use `-o` followed by the path to the directory.
- Failed downloads will be saved in the `err.log` file in the current directory.

Check `fichub_cli metadata --help` for more info.

## Example

- To fetch metadata using an URL

```
fichub_cli metadata -i https://archiveofourown.org/works/10916730/chapters/24276864
```

- To fetch metadata using a file containing URLs

```
fichub_cli metadata -i urls.txt
```

- To choose a output directory

```
fichub_cli metadata -i urls.txt -o "~/Desktop/books"
```

# Links

- [Fichub-cli](https://github.com/FicHub/fichub-cli/)
- [Official Discord Server](https://discord.gg/sByBAhX)
