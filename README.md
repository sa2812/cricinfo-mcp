# Cricinfo MCP Server

This repository contains a simple MCP server with a tool to access the [ESPN Cricinfo](https://www.espncricinfo.com) series archive.

Upon entering a year, a web request is made to the Cricinfo series page for the year (and the preceeding and following years for series that span the New Year). This is returned as a list of structured dataclasses from data that is scraped on the page.
