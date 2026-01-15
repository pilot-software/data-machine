#!/bin/bash
# Download SNOMED CT India Drug Data
# Run this before install.sh

set -e

echo "=========================================="
echo "SNOMED CT India Drug Data Downloader"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if data already exists
if [ -d "CommonDrugCodesForIndia_FlatFilePackage" ]; then
    echo -e "${YELLOW}⚠ CommonDrugCodesForIndia_FlatFilePackage already exists${NC}"
    read -p "Re-download? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping CommonDrugCodesForIndia download"
    else
        rm -rf CommonDrugCodesForIndia_FlatFilePackage
    fi
fi

if [ -d "SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z" ]; then
    echo -e "${YELLOW}⚠ SNOMED RF2 data already exists${NC}"
    read -p "Re-download? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping RF2 download"
    else
        rm -rf SnomedCT_IndiaDrugExtensionRF2_*
    fi
fi

echo ""
echo "=========================================="
echo "Download Options"
echo "=========================================="
echo ""
echo "Option 1: Download from NRCES (Official - Requires Registration)"
echo "  URL: https://www.nrces.in/standards/snomed-ct"
echo "  - Register for free account"
echo "  - Download both packages"
echo "  - Extract to project root"
echo ""
echo "Option 2: Use Shared Drive (If Available)"
echo "  - Contact your team for shared drive link"
echo "  - Download and extract"
echo ""
echo "Option 3: Manual Download"
echo "  1. CommonDrugCodesForIndia_FlatFilePackage.zip (~500MB)"
echo "  2. SnomedCT_IndiaDrugExtensionRF2_*.zip (~1GB)"
echo ""
echo "=========================================="
echo ""

# Check if wget or curl available
if command -v wget &> /dev/null; then
    DOWNLOADER="wget"
elif command -v curl &> /dev/null; then
    DOWNLOADER="curl -O"
else
    echo -e "${RED}❌ Neither wget nor curl found. Please install one.${NC}"
    exit 1
fi

# Option to provide direct download URL (if you have one)
echo "Do you have a direct download URL? (y/N): "
read -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Enter URL for CommonDrugCodesForIndia_FlatFilePackage.zip:"
    read COMMON_URL
    
    echo "Enter URL for SnomedCT RF2 package (or press Enter to skip):"
    read RF2_URL
    
    echo ""
    echo "Downloading..."
    
    if [ ! -z "$COMMON_URL" ]; then
        $DOWNLOADER "$COMMON_URL"
        unzip -q CommonDrugCodesForIndia_FlatFilePackage.zip
        rm CommonDrugCodesForIndia_FlatFilePackage.zip
        echo -e "${GREEN}✓ CommonDrugCodesForIndia extracted${NC}"
    fi
    
    if [ ! -z "$RF2_URL" ]; then
        $DOWNLOADER "$RF2_URL"
        unzip -q SnomedCT_*.zip
        rm SnomedCT_*.zip
        echo -e "${GREEN}✓ SNOMED RF2 extracted${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}Manual Download Required:${NC}"
    echo ""
    echo "1. Visit: https://www.nrces.in/standards/snomed-ct"
    echo "2. Register/Login"
    echo "3. Download:"
    echo "   - CommonDrugCodesForIndia_FlatFilePackage.zip"
    echo "   - SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_*.zip"
    echo "4. Extract both to this directory"
    echo "5. Run: ./install.sh"
    echo ""
    exit 0
fi

# Verify downloads
echo ""
echo "Verifying downloads..."

if [ -d "CommonDrugCodesForIndia_FlatFilePackage" ]; then
    echo -e "${GREEN}✓ CommonDrugCodesForIndia_FlatFilePackage found${NC}"
else
    echo -e "${RED}❌ CommonDrugCodesForIndia_FlatFilePackage missing${NC}"
fi

if [ -d "SnomedCT_IndiaDrugExtensionRF2_PRODUCTION_IN1000189_20251219T120000Z" ]; then
    echo -e "${GREEN}✓ SNOMED RF2 data found${NC}"
else
    echo -e "${YELLOW}⚠ SNOMED RF2 data missing (optional)${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Data download complete!${NC}"
echo "=========================================="
echo ""
echo "Next step: ./install.sh"
echo ""
