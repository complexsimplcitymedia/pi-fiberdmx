#!/bin/bash
# Script to remove GNOME desktop and reclaim disk space
# Keeps Raspberry Pi Desktop (LXDE/OpenBox) and XRDP

set -e

echo "======================================"
echo "GNOME Desktop Removal Script"
echo "======================================"
echo ""
echo "This will remove GNOME but keep Pi Desktop and XRDP"
echo "Press Ctrl+C within 10 seconds to cancel..."
sleep 10

echo ""
echo "Creating backup of package list..."
dpkg --get-selections > /home/laser-dmx/packages_before_removal.txt

echo ""
echo "Removing GNOME Desktop (keeping Pi Desktop & XRDP)..."
sudo apt-get remove -y --purge gnome gnome-core gnome-shell gnome-session \
    gnome-control-center gnome-terminal gnome-software \
    gnome-calculator gnome-calendar gnome-characters gnome-chess \
    gnome-clocks gnome-contacts gnome-disk-utility gnome-font-viewer \
    gnome-games gnome-logs gnome-mahjongg gnome-maps gnome-mines \
    gnome-music gnome-nibbles gnome-robots gnome-sudoku gnome-tetravex \
    gnome-2048 gnome-klotski gnome-taquin gnome-text-editor \
    gnome-tweaks gnome-weather gnome-sushi totem gnome-remote-desktop \
    gnome-user-share gnome-sound-recorder

echo ""
echo "Removing GNOME task metapackage..."
sudo apt-get remove -y --purge task-gnome-desktop

echo ""
echo "Removing LibreOffice GNOME integration..."
sudo apt-get remove -y --purge libreoffice-gnome || true

echo ""
echo "Removing KDE/Polkit GUI tools (keeping mate-polkit for Pi Desktop)..."
sudo apt-get remove -y --purge polkit-kde-agent-1 debconf-kde-helper || true

echo ""
echo "Cleaning up dependencies..."
sudo apt-get autoremove -y --purge

echo ""
echo "Cleaning package cache..."
sudo apt-get clean

echo ""
echo "Final disk usage:"
df -h / | tail -1

echo ""
echo "Package list saved to /home/laser-dmx/packages_before_removal.txt"
echo "GNOME removed successfully!"
echo ""
echo "Kept: Raspberry Pi Desktop (LXDE/OpenBox), XRDP, X11"
