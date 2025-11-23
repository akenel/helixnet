#!/usr/bin/env bash
# ==========================================================
# network_info.sh - Detailed Network Interface Report
# Purpose: Classifies interfaces for clarity (Physical, Docker Bridges, Veth).
# ==========================================================
# ==========================================================
# network_info.sh - DETAILED NETWORK INTERFACE REPORT (NO COLORS)
# ==========================================================

# NOTE: The HYPERLINK function is retained for clickable links, but no colors are used in output.

report_network_info_detailed() {
    local interface_data
    
    # Get all interface data (excluding loopback)
    interface_data=$(ip -br a | grep -v 'lo')

    print_header "🌐 NETWORK INTERFACES & CLASSIFICATION"
    
    printf "  Classification Key: Host/Physical | Docker Bridge | Container Veth\n\n"

    # Simplified format string for 4 arguments: Interface, State, Classification, IP Address(es)
    printf "%-15s %-10s %-25s %s\n" "Interface" "State" "Classification" "IP Address(es)"

    # Process each interface line
    while read -r line; do
        # Use awk to separate the fields: $1=Name, $2=State, $3=IP(s)
        local name=$(echo "$line" | awk '{print $1}')
        local state=$(echo "$line" | awk '{print $2}')
        # Capture the rest of the line as the IP address(es)
        local ip_address=$(echo "$line" | awk '{$1=$2=""; print $0}' | xargs) 
        local classification="Other/Unknown"

        if [[ "$name" =~ ^(eth|wlan|wlp|enp) ]]; then # Added enp for consistency
            classification="Host/Physical 💻"
        elif [[ "$name" =~ ^br-|^docker0 ]]; then    # Added docker0
            classification="Docker Bridge 🌉"
        elif [[ "$name" =~ ^veth ]]; then
            classification="Container Veth 🔗"
        fi

        # The clean, correct printf command with 4 arguments matching the format string
        printf "%-15s %-10s %-25s %s\n" \
            "$name" \
            "$state" \
            "$classification" \
            "$ip_address"

    done <<< "$interface_data"
}

# -----------------------------------------------------------------------------
# 6. RESEARCH LINKS (New Section for Junior Devs)
# -----------------------------------------------------------------------------
report_research_links() {
    print_header "📚 FURTHER RESEARCH & DOCS (For Junior Devs)"

    printf "${YELLOW}* Docker Bridge Networks:${NC} Learn how Docker containers communicate with the host.\n"
    printf "  -> ${CYAN}https://docs.docker.com/network/bridge/${NC}\n\n"
    
    printf "${YELLOW}* Virtual Ethernet Pairs (veth):${NC} Understand container-to-host connectivity.\n"
    printf "  -> ${CYAN}https://www.kernel.org/doc/html/latest/networking/veth.html${NC}\n"
}