#!/bin/python3

# Required: 

ROM_NAME = "DSCDP_CRUJN6_00"
IGNORE_MD5 = False

# Custom Rules Begin Here
# This example one just excludes control characters (except 0x0A)

# Required: this method must exist, and return true / false on if a byte array
# is to be considred valid characters
def check_valid(obytes):
	for b in obytes:
		if b >= 0x00 and b <= 0x1F:
			if not b == 0x0A:
				return False
	return True



