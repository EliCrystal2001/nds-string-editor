#!/bin/python3
import os
import json
import struct
import hashlib
import random
#import ndspy.rom
#import ndspy.code

ROM_NAME = "DSCDP_CRUJN6_00"
rom_data = bytearray(open(ROM_NAME+".nds", "rb").read())
sections = []

def find_all(data, to_find):
	addresses = []
	baddr = 0
	while True:
		try:
			addr = (data.index(to_find))
			baddr += addr+len(to_find)
			data = data[baddr:]
			addresses.append(baddr-len(to_find))
		except ValueError:
			return addresses

def strcpy(new, buffer, offset):
	for i in range(0, len(new)):
		buffer[i+offset] = new[i]
	buffer[offset+len(new)] = 0 # write null-byte

def memcpy(new, buffer, offset):
	for i in range(0, len(new)):
		buffer[i+offset] = new[i]

def find_areas_with_zeros(section):
	start = section["file_loc"]
	end = start+section["length"]
	
	block = rom_data[start:end]

	zero_areas = []
	total_zeros = 0
	offset = 0
	for b in block:
		if b == 0:
			total_zeros += 1
		else:
			if not total_zeros <= 0:
				if not total_zeros-1 <= 0:
					zero_areas.append({"start": (offset-total_zeros)+1, "length": total_zeros-1})
			total_zeros = 0
		offset += 1
	return sorted(zero_areas, key=lambda d: d['length'], reverse=True) 
	

def find_free_area(section, size):

	if not section["name"] == sections[0]["name"]: # First search in section 0! 
		location_in_arm9 = find_free_area(sections[0], size)
		if not location_in_arm9 == None:
			return location_in_arm9

	memory_address = section["ram_loc"]
	start = section["file_loc"]
	end = start+section["length"]
	
	block = rom_data[start:end]
	valid_locations = find_areas_with_zeros(section)
	for valid_location in valid_locations:
		can_use = True
		zstart = valid_location["start"]
		zlen = valid_location["length"]
		zend = zstart+zlen
		mloc = memory_address + zstart 
		
		for i in range(0, size): # try to find an area not in use
			pointers = find_all(block, struct.pack("I", (mloc+i)))
			if len(pointers) >= 1:
				can_use = False
				break
				
		if size >= zlen:
			continue
			
		if can_use == True:
			return (start + zstart, mloc)
		else:
			continue
		
	return None



def apply_mods(section):
	for string in section["strings"]:
		if string["mod"] == None:
			continue
		else:
			old_text = string["str"]
			new_text = string["mod"]
			old_blen = string["blen"]
			rom_addr = string["rom_address"]
			mem_addr = string["memory_address"]
			md5_hash = string["md5"]
			xrefs = string["xrefs"]
			
			og_bytes = rom_data[rom_addr:rom_addr+old_blen]
			hstr = hashlib.md5(og_bytes).hexdigest()[:8]
			
			if not hstr == md5_hash:
				print(old_text + " MD5 Mismatch, NOT CHANGED!")
				continue
			
			text_sjis = new_text.encode("SHIFT_JIS")
			new_blen = len(text_sjis)+1
			print("Changing: "+old_text+" to "+new_text)
			if new_blen <= old_blen:
				print(new_text + " is smaller than "+ old_text+". changing in-place")
				strcpy(text_sjis, rom_data, rom_addr)
			else:
				print(new_text + " is larger than "+old_text+" reallocating")
				print("Locating new area for text")
				new_file_addr, new_mem_addr = find_free_area(section, new_blen)
				print("Found : "+hex(new_file_addr)+", "+hex(new_mem_addr))
				strcpy(text_sjis, rom_data, new_file_addr)
				for xref in xrefs:
					old_addr = struct.unpack("I", rom_data[xref:xref+4])[0]
					if not old_addr == mem_addr:
						print("address at "+hex(xref)+" is "+hex(old_addr)+" not "+hex(mem_addr)+" NOT CHANGING!")
						continue
					print("Changing "+hex(old_addr)+" to "+hex(new_mem_addr))
					new_addr = struct.pack("I", new_mem_addr)
					memcpy(new_addr, rom_data, xref)
def read_jsons(jsonname):
	json_list = json.loads(open(jsonname, "rb").read())	
	for json_name in json_list:
		sections.append(json.loads(open(json_name, "rb").read()))


read_jsons(ROM_NAME + ".json")
for section in sections:
	apply_mods(section)

print("Patches done. writing to file.")
open(ROM_NAME + "_patched.nds", "wb").write(rom_data)

#print(json_data)
