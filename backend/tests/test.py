

def hexToASCII(hexString):
 
        # initialize the ASCII code string as empty.
        ascii = ""
     
        for i in range(0, len(hexString), 2):
     
            # extract two characters from hex string
            part = hexString[i : i + 2]
     
            # change it into base 16 and
            # typecast as the character 
            ch = chr(int(part, 16))
     
            # add this char to final ASCII string
            ascii += ch
         
        return ascii
    
packet_bytes = bytes(332).hex()
    
decodedData =  hexToASCII(hexString=packet_bytes)

print(decodedData)