# Makefile for building a PyQt5 Application with PyInstaller

# Define variables
PYINSTALLER := pyinstaller
SRC := src/app/main.py
NAME := CrawlerApp
DIST_DIR := dist
BUILD_DIR := build
SPEC_FILE := $(NAME).spec

# Default target
all: clean build

# Build target
build:
	$(PYINSTALLER) --name $(NAME) \
	--noconfirm \
	--onefile \
	--windowed \
	--add-data "src/app;app" \
	$(SRC)

# Clean up build files
clean:
	@if exist $(DIST_DIR) rmdir /s /q $(DIST_DIR)
	@if exist $(BUILD_DIR) rmdir /s /q $(BUILD_DIR)
	@if exist $(SPEC_FILE) del $(SPEC_FILE)

# Run the application after build
run:
	$(DIST_DIR)\$(NAME).exe
