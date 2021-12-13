from enum import Flag
import re
from typing import Literal, Match
import instfile



class Entry:
    def __init__(self, string, token, attribute, block):
        self.string = string
        self.token = token
        self.att = attribute
        self.block = block


symtable = []
modarray = []
ltrArray = []

is_literal = False

# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))

def lookup(s):
    for i in range(0,symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1

def insert(s, t, a, b):
    symtable.append(Entry(s,t,a,b))
    return symtable.__len__()-1

def init():
    for i in range(0,instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i], None)
    for i in range(0,instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i], None)

file = open('input.txt', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1

locctr = [0, 0, 0]
blocktype = 0

lookahead = ''
startLine = True
startAddress = 0
programSize = 0
index = ""
base = 0
disp = 0
is_using_base = False
Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 1

Nbitset = 2
Ibitset = 1 

val1 = 0 
val2 = 0

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000

inst = 0
objectCode = True
flags = True
idx = 0
def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False

def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '//':
            startLine = True
            while filecontent[bufferindex] != '\n':
                bufferindex = bufferindex + 1
            lineno += 1
            bufferindex = bufferindex + 1
        elif filecontent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif filecontent[bufferindex] in ['+', '#', ',', '@', "*", '=']:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == 'C') and (filecontent[bufferindex+1] == '\''):
            bytestring = ''
            bufferindex += 2
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue, None)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex] == '\''): # a string can start with C' or only with '
            bytestring = ''
            bufferindex += 1
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex].upper() == 'X') and (filecontent[bufferindex+1] == '\''):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue)%2 == 1:
                bytestringvalue = '0'+ bytestringvalue
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'HEX', bytestringvalue, None)  # should we deal with literals?
            tokenval = p
        else:
            p=lookup(filecontent[bufferindex].upper())
            if p == -1:
                if startLine == True:
                    p=insert(filecontent[bufferindex].upper(),'ID',locctr[blocktype], None) # should we deal with case-sensitive?
                else:
                    p=insert(filecontent[bufferindex].upper(),'ID',-1, None) #forward reference
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr[blocktype]
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return (symtable[p].token)


def error(s):
    global lineno
    print('line ' + str(lineno) + ': '+s)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error')


def checkindex():
    global bufferindex, symtable, tokenval, inst, Xbit3set, index
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index regsiter should be X')
        match('REG')
        inst += Xbit3set
        return True
    return False

def checkReg(shiftSize):
    global bufferindex, symtable, tokenval, inst, Xbit3set, index
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att not in [0,1,2,3,4,5,6,7]:
            error('index regsiter should be one of the following\n A, X, L, B, S, T, F')
        inst += symtable[tokenval].att << shiftSize
        match('REG')
        return True
    return False

def header():
    global locctr,objectCode, tokenval, filecontent, bufferindex, inst, startAddress,programSize, is_using_base
    if pass1or2 == 2:
        print("----Object Code----")
    index = tokenval
    match('ID')
    match('START')
    locctr[blocktype] = tokenval
    startAddress = tokenval
    symtable[index].att = tokenval
    match('NUM')
    if pass1or2 == 2 and objectCode:
        print("H" + symtable[index].string + "   " + str("{:06X}".format(startAddress)) + "   " + str("{:06X}".format(programSize)))
    




def body():
    global idx, base, pass1or2, is_using_base, startLine, is_using_base, blocktype, val1, val2, is_literal, ltrArray, inst
    while True:
        if lookahead == 'ID':
            idx = tokenval
            symtable[tokenval].block = blocktype
            match('ID')
            rest1()
        elif lookahead in ['F1', 'F2', 'F3', '+','F5']:
            stmt()

        elif lookahead == "BASE":
            is_using_base = True
            startLine = False
            match("BASE")
            if lookahead == "NUM":
                base = tokenval
                match("NUM")
            elif lookahead == "*":
                base = locctr[blocktype]
                match("*")
            elif lookahead == "ID": 
                base = symtable[tokenval].att
                match("ID") 

        elif lookahead == "USE":
            match("USE")
            if lookahead == "CDATA":
                blocktype = 1
                match("CDATA")
            elif lookahead == "CBLKS":
                blocktype = 2
                match("CBLKS")
            else:
                blocktype = 0
        
        elif lookahead == "ORG":
            match("ORG")
            if lookahead == "NUM":
                val1 = tokenval
                match("NUM")
                restorg()
        
        elif lookahead == "LTORG":
            match("LTORG")
            for i in ltrArray:
                symtable[i].ltrAddress = locctr[blocktype]
                locctr[blocktype] += int(len(symtable[i].att)/2)
            
            if pass1or2 == 2:
                for i in ltrArray:
                    if symtable[i].token == "STRING":
                        print("T{:06X}   {:02X}   {}".format(symtable[i].ltrAddress, int(len(symtable[i].att)/2), symtable[i].att))
                    elif symtable[i].token == "HEX":
                        print("T{:06X}   {:02X}   {}".format(symtable[i].ltrAddress, int(len(symtable[i].att)/2), symtable[i].att))
                ltrArray = []

        elif lookahead == '=':
            match('=')
            is_literal = True
            if pass1or2 == 1:
                ltrArray.append(tokenval)
            if lookahead == 'STRING':
                match("STRING")
            elif lookahead == "HEX":
                match("HEX")


        elif lookahead == 'END':
            for i in ltrArray:
                symtable[i].ltrAddress = locctr[blocktype]
                locctr[blocktype] += int(len(symtable[i].att)/2)
            
            if pass1or2 == 2:
                for i in ltrArray:
                    if symtable[i].token == "STRING":
                        print("T{:06X}   {:02X}   {}".format(symtable[i].ltrAddress, int(len(symtable[i].att)/2), symtable[i].att))
                    elif symtable[i].token == "HEX":
                        print("T{:06X}   {:02X}   {}".format(symtable[i].ltrAddress, int(len(symtable[i].att)/2), symtable[i].att))
                ltrArray = []

            break
        else:
            error('Syntax error')


def restorg():
    global val1, val2, locctr, blocktype
    if lookahead == "+":
        match("+")
        restorg2()
        locctr[blocktype] = val1 + val2
    elif lookahead =='-':
        match('-')
        restorg2()
        locctr[blocktype] = val1 - val2
    else:
        locctr[blocktype] = val1

def restorg2():
    global val1, val2, locctr
    if lookahead == "NUM":
        val2 = tokenval
        match("NUM")


def tail():
    global pass1or2, locctr, programSize, startAddress, is_using_base, base, blocktype
    match('END')
    if pass1or2==2 and objectCode:
        print("E{:06X}".format(symtable[tokenval].att))
    match('ID')
    programSize = (locctr[0] + locctr[1] + locctr[2]) - startAddress

    for i in symtable:
        if i.block == 1:
            i.att += locctr[0]
    
    for i in symtable:
        if i.block == 2:
            i.att += (locctr[0] + locctr[1])
    
    if pass1or2 == 2:
        for i in modarray:
            print("M{:06X} 05".format(i))


    if pass1or2 == 2 and is_using_base:
        print(f"<<<The BASE register is declared and has the value of 0x{hex(base)[2:].capitalize()}>>>")


def rest1():
    global base, locctr, filecontent, bufferindex, blocktype
    if lookahead == 'F3':
        stmt()
    elif lookahead in ['WORD', 'RESW', 'RESB', 'BYTE']:
        data()




def data():
    global locctr, tokenval, inst, pass1or2, objectCode, blocktype, idx
    if lookahead == 'WORD':
        locctr[blocktype] += 3
        match('WORD')
        
        if pass1or2 == 2 and objectCode:
            print("T{:06X}   03   {:06X}".format(symtable[idx].att, tokenval))
        elif pass1or2 == 2:
            print(tokenval)
        match('NUM')
    elif lookahead == "RESW":
        match('RESW')
        locctr[blocktype] += (tokenval*3)
        if pass1or2 == 2 and objectCode:
            pass
        elif pass1or2 == 2:
            for i in range(tokenval):
                print("000000")
        match('NUM')
    elif lookahead == 'RESB':
        match('RESB')
        locctr[blocktype] += tokenval
        if pass1or2 == 2 and objectCode:
            pass
        elif pass1or2 == 2:
            for i in range(tokenval):
                print("00")
        match('NUM')
    elif lookahead == 'BYTE':
        match('BYTE')
        rest2()



def stmt():
    global locctr, lookahead, startLine, inst, pass1or2, objectCode, index, blocktype
    startLine = False
    
    if lookahead == "F1":
        locctr[blocktype] += 1
        inst = symtable[tokenval].att
        match("F1")
        if pass1or2 == 2 and objectCode:
            print("T{:06X}   01   {:02X}".format(locctr[blocktype]-1, inst))   

    if lookahead == "F2":
        locctr[blocktype] += 2
        inst = symtable[tokenval].att << 8
        match("F2")
        inst += symtable[tokenval].att << 4
        match("REG")
        checkReg(0)
        
        if pass1or2 == 2 and objectCode:
            print("T{:06X}   02   {:04X}".format(locctr[blocktype]-2, inst)) 
        return


    if lookahead == "F3":
        locctr[blocktype] += 3
        idx = tokenval
        if lookahead != '=':
            inst = symtable[tokenval].att << 16
        match('F3')
        rest3(idx)
        if pass1or2==2 and objectCode and lookahead != "=":
            print("T{:06X}   03   {:06X}".format(locctr[blocktype]-3, inst))
        elif pass1or2==2 and lookahead != "=":
            print('{:06X}'.format(inst))
        elif pass1or2 == 2:
            PrintForLtr()
        return

    if lookahead == "+":
        if pass1or2 == 2:
            modarray.append(locctr[blocktype]+1)
        locctr[blocktype] += 4
        match('+')
        inst = symtable[tokenval].att << 24
        inst += Ebit4set << 20
        match('F3')
        rest5()
        if pass1or2 == 2 and objectCode:
            print("T{:06X}   04   {:08X}".format(locctr[blocktype]-4, inst))
        elif pass1or2 == 2:
            print('{:06X}'.format(inst))
        return






def PrintForLtr():
    global locctr, lookahead, tokenval, inst
    inst += (Nbitset + Ibitset) << 16
    inst += Pbit3set
    print("T{:06X}   03   {:06X}".format(locctr[blocktype]-3, inst))




def rest2():
    global locctr, tokenval, symtable, pass1or2, objectCode, blocktype



    if lookahead == "STRING":
        locctr[blocktype] += int(len(symtable[tokenval].att)/2)
        if pass1or2 == 2 and objectCode:
            print("T{:06X}   {:02X}   {}".format(locctr[blocktype]-int(len(symtable[tokenval].att)/2), int(len(symtable[tokenval].att)/2), symtable[tokenval].att))
        elif pass1or2 == 2:
            print(symtable[tokenval].att)
        match('STRING')
    elif lookahead == 'HEX':
        locctr[blocktype] += int(len(symtable[tokenval].att)/2)
        if pass1or2 == 2 and objectCode:
            print("T{:06X}   {:02X}   {}".format(locctr[blocktype]-int(len(symtable[tokenval].att)/2), int(len(symtable[tokenval].att)/2), symtable[tokenval].att))
        elif pass1or2 == 2:
            print(symtable[tokenval].att)
        match('HEX')

def rest3(idx):
    global tokenval, symtable, inst, pass1or2, blocktype
    if symtable[idx].string != "RSUB":
        if lookahead == "ID":
            inst += (Nbitset + Ibitset) << 16
            rest4()
        elif lookahead == "NUM":
            inst += (Nbitset + Ibitset) << 16
            inst += tokenval
            match("NUM")
            checkindex()
        elif lookahead == "#":
            match("#")
            inst += Ibitset << 16
            rest4()
        elif lookahead == "@":
            match("@")
            inst += Nbitset << 16
            rest4()

 

def rest5():
    global tokenval, symtable, inst, pass1or2, flags, blocktype

    if lookahead == "ID":
        if flags:
            inst += (Nbitset + Ibitset) << 24
        flags = True
        inst += symtable[tokenval].att 
        match('ID')
        checkindex()
    elif lookahead == "NUM":
        if flags:
            inst += (Nbitset + Ibitset) << 24
        flags = True
        inst += tokenval
        match("NUM")
        checkindex()
    elif lookahead == "#":
        match("#")
        inst += Ibitset << 24
        flags = False
        rest5()
    elif lookahead == "@":
        match("@")
        inst += Nbitset << 24
        flags = False
        rest5()
            
def in_range(disp, register):
    if register == "PC":
        if disp <= 2047 and disp >= -2048:
            return True
    elif register == "BASE":
        if disp >= 0 and disp <= 4096:
            return True
    return False

def rest4():
    global lookahead, inst, disp, locctr, pass1or2, base, is_using_base, blocktype
    if lookahead == "ID":
        if pass1or2 == 2:
            disp = symtable[tokenval].att - locctr[blocktype]
            if in_range(disp, "PC"):
                inst += Pbit3set
                
                inst += disp
            elif is_using_base:
                disp = symtable[tokenval].att - base
                if in_range(disp, "BASE"):
                    inst += Bbit3set
                    inst += disp
                else:
                    error("Displacement address is out of range")
        match("ID")
        checkindex()
    elif lookahead == "NUM":
        inst += tokenval
        match("NUM")
        checkindex()



def parse():
    global lookahead
    lookahead = lexan()
    header()
    body()
    tail()


    



def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno, blocktype
    init()
    w = file.read()
    filecontent=re.split("([\W])", w)
    i=0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if filecontent[len(filecontent)-1] != '\n': #to be sure that the content ends with new line
        filecontent.append('\n')
    for pass1or2 in range(1,3):
        parse()
        bufferindex = 0
        locctr[0] = 0
        locctr[1] = 0
        locctr[2] = 0
        blocktype = 0
        lineno = 1

    file.close()


main()

