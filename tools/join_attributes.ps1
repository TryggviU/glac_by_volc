#-------------------------------------------------------#
# A script that joins regional volcano attribute files. #
#                                                       #
# The script assumes the user is somewhere within the   #
# project directory.									#
#														#
# Input: none											#
# Run command:											#
#  PS ..\ps1> .\join_attributes.ps1						#
#-------------------------------------------------------#

# Default values.
$RootName = "glac_by_volc"
$RGI_v = "RGI2000-v7.0"

function Set-Root {
	param(
		[string]$Path,
		[string]$Name
	)
	
	# Set the working directory as the project directory.
	if ((Split-Path $Path -Leaf) -eq $Name) {
		return $Path
	}
	else {
		return Set-Root -Path (Split-Path $Path) -Name $Name
	}
}

# Set the working directory as the project directory.
$dir_root = Set-Root -Path (Get-Location) -Name $RootName
# Set the root directory as the current directory.
Set-Location -Path $dir_root

# Processed data directory.
$dir_dp = Join-Path -Path $dir_root -ChildPath "data_processed" | Join-Path -ChildPath "regional_files" | Join-Path -ChildPath "$RGI_v-GV"

# Check if the specified RGI subdirectory exists.
if (-not (Test-Path -Path $dir_dp)){
	Write-Error "Error: The processed data directory does not exist. Please specify an existing path." -ErrorAction Stop
}

# Iterate through all the RGI subdirectories.
foreach ($subdir_rgi in (Get-ChildItem -Path $dir_dp).FullName) {
	# Save the RGI regional code.
	$rgi = "$subdir_rgi".Split("-")[-1]
	
	# Iterate through all the radii subdirectories.
	foreach ($subdir_rad in (Get-ChildItem -Path $subdir_rgi -Directory).FullName) {
		# Save the radius subdir.
		$rgi_rad = (Split-Path $subdir_rad -Leaf)
		Write-Host $rgi_rad
		
		# Set the .csv output file.
		$out_csv = Join-Path -Path $subdir_rgi -ChildPath "$rgi_rad-attributes.csv"
		
		# Delete previous versions of the output file if they exist.
		if (Test-Path $out_csv) {
			Remove-Item $out_csv
		}
		
		# Iterate through all the volcano attribute files and append them to the output csv file.
		foreach ($csv in (Get-ChildItem -Path $subdir_rad -Recurse -Include *attributes.csv).FullName) {
			Import-Csv $csv | Export-Csv -Path $out_csv -Append -NoTypeInformation
		}
	}
}

