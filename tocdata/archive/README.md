This `archive` folder in the `tocdata` directory is used to save `spotted_tocs` and `done_pubs` CSV files when the user selects the `Update CSV data` from the `File` Menu in the `MagTOCspotter`app.

The in memory tocdata is read from the `MagTOCdata` repository on GitHub, then the currennt CSV files in the `tocdata` folder are backed up to this archive folder. The filenames of the archived CSV files are suffixed with a datestamp string in the 'mmddyy' format.
 