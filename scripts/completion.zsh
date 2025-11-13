#!/usr/bin/env zsh
# Zsh completion script for mcp-browser
# Installation:
#   source scripts/completion.zsh
# Or add to .zshrc:
#   eval "$(mcp-browser completion zsh)"

_mcp_browser() {
    local -a commands
    commands=(
        'quickstart:Interactive setup wizard for first-time users'
        'init:Initialize MCP Browser extension and configuration'
        'start:Start the MCP Browser server'
        'status:Show current server and installation status'
        'doctor:Diagnose and fix common MCP Browser issues'
        'dashboard:Run the monitoring dashboard'
        'tutorial:Interactive tutorial for using MCP Browser'
        'install:Install MCP config for Claude Code/Desktop'
        'uninstall:Remove MCP config from Claude Code/Desktop'
        'extension:Manage Chrome extension installation'
        'mcp:Run in MCP stdio mode for Claude Code integration'
        'version:Show version information'
    )

    local -a global_options
    global_options=(
        '--help[Show help message]'
        '--version[Show version information]'
        '--debug[Enable debug logging]'
        '--config[Path to configuration file]:file:_files -g "*.json"'
    )

    _arguments -C \
        '1:command:->commands' \
        '*::arg:->args' \
        $global_options

    case $state in
        commands)
            _describe -t commands 'mcp-browser commands' commands
            ;;
        args)
            case $words[1] in
                start)
                    _arguments \
                        '--port[WebSocket port]:port:' \
                        '--dashboard[Enable dashboard]' \
                        '--no-dashboard[Disable dashboard]' \
                        '--dashboard-port[Dashboard port]:port:' \
                        '--background[Run in background]' \
                        '--help[Show help]'
                    ;;
                init)
                    _arguments \
                        '--project[Initialize in current project]' \
                        '--global[Initialize globally]' \
                        '--help[Show help]'
                    ;;
                doctor)
                    _arguments \
                        '--fix[Attempt to fix issues automatically]' \
                        '--verbose[Show detailed diagnostic information]' \
                        '--help[Show help]'
                    ;;
                dashboard)
                    _arguments \
                        '--port[Dashboard port]:port:' \
                        '--open[Open dashboard in browser]' \
                        '--help[Show help]'
                    ;;
                status)
                    _arguments \
                        '--format[Output format]:format:(table json simple)' \
                        '--help[Show help]'
                    ;;
                install)
                    _arguments \
                        '--target[Installation target]:target:(claude-code claude-desktop both)' \
                        '--force[Force installation even if already installed]' \
                        '--help[Show help]'
                    ;;
                uninstall)
                    _arguments \
                        '--target[Uninstall target]:target:(claude-code claude-desktop both)' \
                        '--help[Show help]'
                    ;;
                extension)
                    _arguments \
                        '1:subcommand:(install update path)' \
                        '--help[Show help]'
                    ;;
                version)
                    _arguments \
                        '--detailed[Show detailed version information]' \
                        '--help[Show help]'
                    ;;
                *)
                    _arguments '--help[Show help]'
                    ;;
            esac
            ;;
    esac
}

compdef _mcp_browser mcp-browser