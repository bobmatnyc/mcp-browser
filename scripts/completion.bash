#!/bin/bash
# Bash completion script for mcp-browser
# Installation:
#   source scripts/completion.bash
# Or add to .bashrc/.bash_profile:
#   eval "$(mcp-browser completion bash)"

_mcp_browser_completions() {
    local cur prev opts base_commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Base commands
    base_commands="quickstart init start status doctor dashboard tutorial install uninstall extension mcp version --help --version --debug"

    # Command-specific options
    case "${prev}" in
        mcp-browser)
            COMPREPLY=( $(compgen -W "${base_commands}" -- ${cur}) )
            return 0
            ;;
        start)
            local start_opts="--port --dashboard --no-dashboard --dashboard-port --background --help"
            COMPREPLY=( $(compgen -W "${start_opts}" -- ${cur}) )
            return 0
            ;;
        init)
            local init_opts="--project --global --help"
            COMPREPLY=( $(compgen -W "${init_opts}" -- ${cur}) )
            return 0
            ;;
        doctor)
            local doctor_opts="--fix --verbose --help"
            COMPREPLY=( $(compgen -W "${doctor_opts}" -- ${cur}) )
            return 0
            ;;
        dashboard)
            local dashboard_opts="--port --open --help"
            COMPREPLY=( $(compgen -W "${dashboard_opts}" -- ${cur}) )
            return 0
            ;;
        status)
            local status_opts="--format --help"
            COMPREPLY=( $(compgen -W "${status_opts}" -- ${cur}) )
            return 0
            ;;
        install)
            local install_opts="--target --force --help"
            COMPREPLY=( $(compgen -W "${install_opts}" -- ${cur}) )
            return 0
            ;;
        uninstall)
            local uninstall_opts="--target --help"
            COMPREPLY=( $(compgen -W "${uninstall_opts}" -- ${cur}) )
            return 0
            ;;
        extension)
            local extension_opts="install update path --help"
            COMPREPLY=( $(compgen -W "${extension_opts}" -- ${cur}) )
            return 0
            ;;
        version)
            local version_opts="--detailed --help"
            COMPREPLY=( $(compgen -W "${version_opts}" -- ${cur}) )
            return 0
            ;;
        --format|-f)
            COMPREPLY=( $(compgen -W "table json simple" -- ${cur}) )
            return 0
            ;;
        --config)
            # Complete with json files
            COMPREPLY=( $(compgen -f -X '!*.json' -- ${cur}) )
            return 0
            ;;
        --port|-p|--dashboard-port)
            # Suggest common ports
            COMPREPLY=( $(compgen -W "8080 8875 8876 8877 8878 8879 8880" -- ${cur}) )
            return 0
            ;;
    esac

    # Handle options starting with --
    if [[ ${cur} == -* ]] ; then
        local global_opts="--help --version --debug --config"
        COMPREPLY=( $(compgen -W "${global_opts}" -- ${cur}) )
        return 0
    fi

    # Default to base commands
    COMPREPLY=( $(compgen -W "${base_commands}" -- ${cur}) )
}

complete -F _mcp_browser_completions mcp-browser