sublime-iRules
==============

# About

iRules Syntax Highlighting for F5 Networks BIG-IP iRules syntax (http://devcentral.f5.com) for the Sublime Text Editor http://www.sublimetext.com

* The command completion and syntax highlighting should be complete as of TMOS v15.1.

* This includes highlighting and command completion:

   ![a relative link](../screenshots/commands.png?raw=true)

   ![a relative link](../screenshots/if.png?raw=true)

   ![a relative link](../screenshots/when.png?raw=true)

* And highligting of deprecated, removed, and illegal functions/events/commands (requires a scheme that supports the "invalid.illegal" and "invalid.deprecated" scopes and not all do. "Monokai" that ships with Sublime Text 3 does, so you can use that to test things out:

   ![a relative link](../screenshots/deprecated.png?raw=true)

* And highlighting of some possible double-substitution issues inside iRules.

* And formatting of code (⌘+⇧+P -> iRule: Format Code)

This bundle was updated on December 16, 2019 and is currently maintained by James Deucker (https://github.com/bitwisecook).

Any suggestions or improvements, please make an issue on the github repo.

This bundle is created from both the built-in Tcl syntax by Sublime and the Visual Studio Code extension also by me (https://github.com/bitwisecook/vscode-iRule).

# Installation (Package Management)

## New Way
iRules is now in the the main repository. (preferred)

- go to the command pallete (⌘+⇧+P)
- select "Package Control: Install Package"
- type "iRules" and select the iRules package

## Old Way
Using Package Control at https://packagecontrol.io/installation:

- Remove the package, if installed manually
- Add a repository: https://github.com/billchurch/sublime-iRules
- Install sublime-iRules with Package Control. It should pull the correct branch from Github

# Notes
 * I don't yet understand how to properly control the completions so events only happen at when
 * I haven't yet figured out how to make it so `when` and `proc` can't nest
 * Many completions are missing
 * the basic formatter is in and working