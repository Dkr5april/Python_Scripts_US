
# ============================================================
# BABA PYTHON v1.0 (MERGED)
# EPM MODI + NEWSANJEEVI Unified Prediction Engine
# Author: Sanjeev Kumar
# ============================================================

# ------------------ NEWSANJEEVI ENGINE (FULL) ------------------
# Original code preserved, namespaced safely

def run_newsanjeevi_full():
    try:
        from pathlib import Path
        file_name = Path.joinpath(Path(__file__).parent,Path(__file__).stem+'.log')
        with open(file_name,'w') as f:
            p1 = (input('Enter  Player A Date of Birth: '))
            p2 = (input('Enter  Player B Date of Birth: '))
            p3 = (input('Enter  Game of Day: '))
    
            #p1="15-10-1994"
            #p2="04-10-1998"
            #p3="23-02-2023"
    
            def convert2int(list):
                s = [str(i) for i in list]
                # Join list items using join()
                res = int("".join(s))
                return(int(res))
    
            def convert2list(string):
                list1=[]
                list1[:0]=string
                return list1
    
            def applyMatrix3Formula1(m3count, m3, tmplist):
                tlist = []
                if m3count == int(tmplist[0]):
                    tlist = m3 + list(str(sum(int(tmplist[1]), int(tmplist[2])))) + list(tmplist[3])
                elif m3count == int(tmplist[1]):
                    tlist = m3 + list(str(sum(int(tmplist[0]), int(tmplist[2])))) + list(tmplist[3])
                elif m3count == int(tmplist[2]):
                    tlist = m3 + list(str(sum(int(tmplist[0]), int(tmplist[1])))) + list(tmplist[3])
                elif m3count == int(tmplist[3]):
                    tlist = m3 + list(str(sum(int(tmplist[0]), int(tmplist[1])))) +  list(tmplist[2])
                return tlist
    
            def applyMatrix3Formula2(m3, tmplist):
                tlist = []
                intm3 = convert2int(m3)
                intlist = convert2int(tmplist)
                r = intlist - intm3
                tlist = convert2list(str(r))
                a = sum(int(tlist[0]), int(tlist[1]))
                b = sum(int(tlist[2]), int(tlist[3]))
                tlist = m3 + list(str(a)) + list(str(b))
                return tlist
                
            def is72(sevenHit, twoHit, x):
                if sevenHit == 0 and x == 7:
                    sevenHit = 1
                    x = 0
                if twoHit == 0 and x == 2:
                    twoHit = 1
                    x = 0 
                return sevenHit, twoHit, x
    
            def sum4(suma, sumb, sumc, sumd):
                tmpA = suma +  sumb +  sumc + sumd
                if tmpA > 9:
                    sumtemp = 0
                    for i in list(str(tmpA)):
                        sumtemp = sumtemp + int(i)
                else:
                    sumtemp = int(tmpA)
    
                tmpA = sumtemp
                if tmpA > 9:
                    sumtemp = 0
                    for i in list(str(tmpA)):
                        sumtemp = sumtemp + int(i)
                else:
                    sumtemp = int(tmpA)
                return sumtemp
    
            def sum3(suma, sumb, sumc):
                tmpA = suma +  sumb +  sumc
                if tmpA > 9:
                    sumtemp = 0
                    for i in list(str(tmpA)):
                        sumtemp = sumtemp + int(i)
                else:
                    sumtemp = int(tmpA)
    
                tmpA = sumtemp
                if tmpA > 9:
                    sumtemp = 0
                    for i in list(str(tmpA)):
                        sumtemp = sumtemp + int(i)
                else:
                    sumtemp = int(tmpA)
                return sumtemp
    
            def sum(suma, sumb):
                tmpA = suma + sumb
                if tmpA > 9:
                    sumtemp = 0
                    for i in list(str(tmpA)):
                        sumtemp = sumtemp + int(i)
                    subtemp = tmpA - 9
                else:
                    sumtemp = int(tmpA)
                return sumtemp
    
            def subtract(suma, sumb):
                tmpA = suma - sumb
                sumtemp = 0
                if tmpA <= 0:
                    sumtemp = 9 + tmpA
                else:
                    sumtemp = int(tmpA)
                return sumtemp
    
            def get18Formula(mylist, a, b, c, d):
                if a != 0:
                    mylist = mylist + list(str(a))
    
                if b != 0:
                    mylist = mylist + list(str(b))
    
                if c != 0:
                    mylist = mylist + list(str(c))
    
                if d != 0:
                    mylist = mylist + list(str(d))
                return mylist
    
            def getXvalue(x, dest):
                if dest == 0:
                    dest = 9
                tmpA = 0
                for i in range(1, 10):
                    tmpA = sum(x, i)
                    if tmpA == dest:
                        return i
                print("FAILED in getXvalue for input and destination", x, dest, file=f)
                exit(1)
    
            def getWLTable(a, b):
                winA =  a - 1
                if winA == 0:
                    winA = 9
                lossA =  a + 1
                if lossA == 10:
                    lossA = 1
    
                winB =  b - 1
                if winB == 0:
                    winB = 9
                lossB =  b + 1
                if lossB == 10:
                    lossB = 1
                    
                return winA, winB, lossA, lossB
    
            
            def add90(a):
                add90 = a + 90
                listadd90 = list(str(add90))
                if add90 < 100:
                    listadd90 = list(str(0)) + list(str(add90))
                print("after 90 add:", listadd90, file=f)
                b = str(listadd90[0])+str(listadd90[2])
                b = int(b)
                bstr = str(b)
                if b < 10:
                    bstr = str(0)+str(b)
                print("bstr ", bstr, file=f)
                print("first and third", b, file=f)
                b1 = int(str(listadd90[1]))
                if b1 < 10:
                    b1str = str(0)+str(b1)
                else:
                    b1str = str(b1)
                if b1 == b:
                    b2 = 90 - b
                elif b1 < b:
                    b2 = b - b1
                else:
                    b2 = b1 - b
                print("2nd and 1st3rd-2nd", b1, b2, file=f)
                if b2 < 10:
                    b2str = str(0)+str(b2)
                else:
                    b2str = str(b2)
                print("2nd and 1st3rd-2nd in string", b1str+b2str, file=f)
                a1list = list(b1str) + list(b2str)
                if b1 <= 0:
                    b1 = 90
                if b1 < b:
                    b1 = b1 * 10
                    if b1 < b:
                        b1 = b1 * 10
                        if b1 < b:
                            b1 = b1 * 10
                print("2nd to minus:", b1, file=f)
                b3 = b1 - b
                if b3 < 10:
                    b3str = str(0)+str(b3)
                else:
                    b3str = str(b3)
                print("1st3rd and (2nd minus 1st3rd)", bstr+b3str, file=f)
                a2list = list(bstr) + list(b3str)
                print("a1list and a2list", a1list, a2list, file=f)
                alist = list(str(sum(int(a1list[0]), int(a2list[0])))) + list(str(sum(int(a1list[1]), int(a2list[1])))) + list(str(sum(int(a1list[2]), int(a2list[2])))) + list(str(sum(int(a1list[3]), int(a2list[3]))))
                return alist
                
            def get_battlefield_value(A,B):
                db = {
                        11:5129,    22:8343,   33:8638,
                        12:4784,    23:6856,   34:7255,
                        13:4967,    24:3593,   35:2536,
                        14:8383,    25:2976,   36:3599,
                        15:6542,    26:2259,   37:1165,
                        16:2734,    27:1824,   38:3981,
                        17:2465,    28:5229,   39:2165,
                        18:4611,    29:7187,   19:9335,
                        44:6969,    55:2254,   66:3239,
                        45:1487,    56:5316,   67:8769,
                        46:7377,    57:5612,   68:1598,
                        47:7313,    58:4518,   69:4874,
                        48:4888,    59:2384,   88:6479,
                        49:2999,    77:3655,   99:9635,
                        78:7161,    89:4293,   79:6354,
                }
    
                # key = [ A*10 + B, A + B*10]
                if not db.get(A*10+B, False):
                    return db.get(A+B*10,False)
                return db.get(A*10+B, False)
    
            def subtract90(a):
                if a > 90:
                    b = 9 - abs(90 - a)
                    if b == 0:
                        c = str(0) + str(9)
                    elif b < 10:
                        c = str(0) + str(b)
                    else:
                        c = str(b)
                else:
                    b = 90 - a
                    if b == 0:
                        c = str(0) + str(9)
                    elif b > 0 and b < 10:
                        c = str(0) + str(b)
                    else:
                        c = str(b)
                clist = list(c)
                d = sum(int(clist[0]), int(clist[1]))
                return d
        
            def get_win_max_value(A,B):
                win_max = {
                            19:5662,    11:5382,   12:2172,
                            28:737,    29:3324,   39:4701,
                            37:4882,    38:7421,   48:2077,
                            46:7670,    47:3108,   57:1254,
                            55:3703,    56:5105,   66:3636,
                            13:7353,    14:8482,   15:6687,
                            22:3077,    23:1828,   24:636,
                            49:321,    59:5481,   33:4501,
                            58:7712,    68:6276,   69:8355,
                            67:3551,    77:4120,   78:5168,
                            16:6850,    17:2673,   18:5882,
                            25:6612,    26:2888,   27:8678,
                            34:1438,    35:2517,   36:6093,
                            79:2330,    44:7178,   45:8115,
                            88:2214,    89:845,   99:9867,
                        }
                # key = [ A*10 + B, A + B*10]
                if not win_max.get(A*10+B, False):
                    return win_max.get(A+B*10,False)
                return win_max.get(A*10+B, False)
    
            def get_set_value(A,B):
                set_value_db = { 19:4649,    11:8424,
                                28:8715,      29:6456,
                                37:3869,       38:1553,        
                                44:6657,       47:6231,
                                55:2771,       56:8237,
    
                                12:1565,      13:2296,
                                39:3284,      22:7821,
                                48:1461,      49:4264,
                                57:9647,      58:2655,
                                66:2129,     67:7494,
    
                                14:9487,      15:2747,
                                23:2824,      24:5686,
                                59:6486,     33:9651,
                                68:7272,     69:4415,
                                77:5125,      78:1228,
    
                                16:7163,     17:8346,
                                25:7825,     26:8552,
                                34:2642,     35:8271,
                                79:3543,     44:4742,
                                88:3427,     89:6518,
    
                                18:8815,
                                27:2692,
                                36:9926,
                                45:2138,
                                99:3881}
                if not set_value_db.get(A*10+B, False):
                    return set_value_db.get(A+B*10,False)
                return set_value_db.get(A*10+B, False)
            def get_ortho_values(A):
                get_ortho = {
                                3:1783,
                                5:2675,
                                7:3567,
                                9:4459,
                                2:4542,
                                4:6234,
                                6:7126,
                                8:8918,
                                1:9891,
                }
                return get_ortho.get(A)
    
                
            def get_turbo_values(A):
                get_turbo = {
                                1:4636,
                                2:9272,
                                3:5727,
                                4:1363,
                                5:6818,
                                6:2454,
                                7:7999,
                                8:3545,
                                9:8181,
                }
                return get_turbo.get(A)
    
    
            Adatelist = p1.split("-")
            Bdatelist = p2.split("-")
            Cdatelist = p3.split("-")
    
            a=Adatelist[0]
            b=Adatelist[1]
            c=Adatelist[2]
    
            a1=Bdatelist[0]
            b1=Bdatelist[1]
            c1=Bdatelist[2]
    
            a2=Cdatelist[0]
            b2=Cdatelist[1]
            c2=Cdatelist[2]
    
            print(a, b, c, a1, b1, c1, a2, b2, c2, file=f)
    
            inta = int(a)
    
            ares = list(a)
            bres = list(b)
            cres = list(c)
    
            atotal = 0
            for i in ares:
                atotal = atotal + int(i)
                
            btotal = 0
            for i in bres:
                btotal = btotal + int(i)
                
            ctotal = 0
            for i in cres:
                ctotal = ctotal + int(i)
    
            intsubtotalA = atotal + btotal + ctotal
            subtotalA = list(str(intsubtotalA))
    
            intTotalA = inta + intsubtotalA
            TotalA = list(str(intTotalA))
            if intTotalA <= 9:
                TotalA = list(str(0)) + list(str(intTotalA))
    
            print ("Matrix 1                                        :", ares, TotalA, file=f)
            DisplayMatrix1 = ares + TotalA
            
            DM1a = subtract90(int(str(DisplayMatrix1[0])+str(DisplayMatrix1[1])))
            DM1b = subtract90(int(str(DisplayMatrix1[1])+str(DisplayMatrix1[3])))
            DM1c = subtract90(int(str(DisplayMatrix1[3])+str(DisplayMatrix1[2])))
            DM1d = subtract90(int(str(DisplayMatrix1[2])+str(DisplayMatrix1[0])))
            DM1ab = list(str(sum(DM1a, DM1b)))
            DM1cd = list(str(sum(DM1c, DM1d)))
            DM1M = DM1ab + DM1cd
            
            PlayerA = sum(int(TotalA[0]), int(TotalA[1]))
            print("Player A Count  TotalA[0]), int(TotalA[1])       :", PlayerA, file=f)
    
            tA = sum(int(ares[0]), int(TotalA[0]))
    
            tA1 = sum(int(ares[1]), int(TotalA[1]))
    
            listA = [ str(tA), str(tA1) ]
    
            matrixA = listA + listA
            matrixAtotal = sum4(int(matrixA[0]) , int(matrixA[1]), int(matrixA[2]), int(matrixA[3]))
    
            print ("Matrix 1 Final Calculation                      :", listA, matrixA, matrixAtotal, file=f)
    
            part4Alist = add90(intTotalA)
            print ("Part-4 for Matrix 1 added 90                    :",part4Alist , file=f)
    
            matrix1WinA, matrix1WinB, matrix1LossA, matrix1LossB = getWLTable(matrixAtotal, matrixAtotal)
            Matrix1rA = sum(matrix1WinA, matrix1LossA)
            Matrix1rB = sum(matrix1WinB , matrix1LossB)
            Matrix1cA = sum(matrix1WinA, matrix1WinB)
            Matrix1cB = sum(matrix1LossA , matrix1LossB)
            print ("======== Matrix A Begin =================", file=f)
            print ("{:<8} {:<15} {:<10}".format('Person','Win','Loss', "="), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format('------','--','----', ""), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( matrixAtotal, matrix1WinA, matrix1LossA, Matrix1rA), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( matrixAtotal, matrix1WinB, matrix1LossB, Matrix1rB), file=f)
            print ("{:<8} {:<15} {:<10}".format('','--','----'), file=f)
            print ("{:<8} {:<15} {:<10}".format( " ", Matrix1cA, Matrix1cB), file=f)
            print ("======== Matrix A End =================", file=f)
    
            matrix1List = list(str(Matrix1cA)) + list(str(Matrix1rA)) + list(str(Matrix1rB)) + list(str(Matrix1cB))
    
            intb = int(a1)
    
            a1res = list(a1)
            b1res = list(b1)
            c1res = list(c1)
    
            a1total = 0
            for i in a1res:
                a1total = a1total + int(i)
                
            b1total = 0
            for i in b1res:
                b1total = b1total + int(i)
                
            c1total = 0
            for i in c1res:
                c1total = c1total + int(i)
    
            intsubtotalB = a1total + b1total + c1total
            subtotalB = list(str(intsubtotalB))
    
            intTotalB = intb + intsubtotalB
            TotalB = list(str(intTotalB))
            if intTotalB <= 9:
                TotalB = list(str(0)) + list(str(intTotalB))
                
            print ("Matrix 2                                        :", a1res, TotalB, file=f)
            DisplayMatrix2 = a1res + TotalB
            
            DM2a = subtract90(int(str(DisplayMatrix2[0])+str(DisplayMatrix2[1])))
            DM2b = subtract90(int(str(DisplayMatrix2[1])+str(DisplayMatrix2[3])))
            DM2c = subtract90(int(str(DisplayMatrix2[3])+str(DisplayMatrix2[2])))
            DM2d = subtract90(int(str(DisplayMatrix2[2])+str(DisplayMatrix2[0])))
            DM2ab = list(str(sum(DM2a, DM2b)))
            DM2cd = list(str(sum(DM2c, DM2d)))
            DM2N = DM2ab + DM2cd
            
            PlayerB = sum(int(TotalB[0]), int(TotalB[1]))
            print("Player B Count TotalB[0] TotalB[1]               :", PlayerB, file=f)
    
            part4Blist = add90(intTotalB)
            print ("Part-4 for Matrix 2 added 90                    :",part4Blist , file=f)
    
            tB = sum(int(a1res[0]) , int(TotalB[0]))
    
            tB1 = sum(int(a1res[1]) , int(TotalB[1]))
    
            listB = [ str(tB), str(tB1) ]
    
            matrixB = listB + listB
    
            matrixBtotal = sum4(int(matrixB[0]) , int(matrixB[1]), int(matrixB[2]), int(matrixB[3]))
    
            print ("Matrix 2 Final Calculation                      :", listB, matrixB, matrixBtotal, file=f)
            matrix2WinA, matrix2WinB, matrix2LossA, matrix2LossB = getWLTable(matrixBtotal, matrixBtotal)
            Matrix2rA = sum(matrix2WinA, matrix2LossA)
            Matrix2rB = sum(matrix2WinB , matrix2LossB)
            Matrix2cA = sum(matrix2WinA, matrix2WinB)
            Matrix2cB = sum(matrix2LossA , matrix2LossB)
            print ("======== Matrix B Begin =================", file=f)
            print ("{:<8} {:<15} {:<10}".format('Person','Win','Loss', "="), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format('------','--','----', ""), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( matrixBtotal, matrix2WinA, matrix2LossA, Matrix2rA), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( matrixBtotal, matrix2WinB, matrix2LossB, Matrix2rB), file=f)
            print ("{:<8} {:<15} {:<10}".format('','--','----'), file=f)
            print ("{:<8} {:<15} {:<10}".format( " ", Matrix2cA, Matrix2cB), file=f)
            print ("======== Matrix B End =================", file=f)
    
            matrix2List = list(str(Matrix2cA)) + list(str(Matrix2rA)) + list(str(Matrix2rB)) + list(str(Matrix2cB))
    
            intc = int(a2)
    
            a2res = list(a2)
            b2res = list(b2)
            c2res = list(c2)
    
            a2total = 0
            for i in a2res:
                a2total = a2total + int(i)
                
            b2total = 0
            for i in b2res:
                b2total = b2total + int(i)
                
            c2total = 0
            for i in c2res:
                c2total = c2total + int(i)
    
            intsubtotalC = a2total + b2total + c2total
            subtotalC = list(str(intsubtotalC))
    
            intTotalC = intc + intsubtotalC
            TotalC = list(str(intTotalC))
            if intTotalC <= 9:
                TotalC = list(str(0)) + list(str(intTotalC))
    
            DisplayMatrix3 = a2res + TotalC
            
            DM3a = subtract90(int(str(DisplayMatrix3[0])+str(DisplayMatrix3[1])))
            DM3b = subtract90(int(str(DisplayMatrix3[1])+str(DisplayMatrix3[3])))
            DM3c = subtract90(int(str(DisplayMatrix3[3])+str(DisplayMatrix3[2])))
            DM3d = subtract90(int(str(DisplayMatrix3[2])+str(DisplayMatrix3[0])))
            DM3ab = list(str(sum(DM3a, DM3b)))
            DM3cd = list(str(sum(DM3c, DM3d)))
            DM3L = DM3ab + DM3cd
            
            ML = sum4(int(str(DM1M[0])), int(str(DM1M[1])), int(str(DM3L[0])), int(str(DM3L[1])))
            NL = sum4(int(str(DM2N[0])), int(str(DM2N[1])), int(str(DM3L[0])), int(str(DM3L[1])))
            
            print ("Matrix 3                                        :", a2res, TotalC, file=f)
            DestinyCountLast2 = sum(int(TotalC[0]), int(TotalC[1]))
            print("Destiny Count last 2 digits                      :", DestinyCountLast2, file=f)
    
            part4Clist = add90(intTotalC)
            print ("Part-4 for Matrix 3 added 90                    :",part4Clist , file=f)
    
            part4AClist = list(str(sum(int(part4Alist[0]), int(part4Clist[0])))) + list(str(sum(int(part4Alist[1]), int(part4Clist[1])))) + list(str(sum(int(part4Alist[2]), int(part4Clist[2])))) + list(str(sum(int(part4Alist[3]), int(part4Clist[3]))))
    
            print("Part-4 AC list                                   :", part4AClist, file=f)
    
            part4BClist = list(str(sum(int(part4Blist[0]), int(part4Clist[0])))) + list(str(sum(int(part4Blist[1]), int(part4Clist[1])))) + list(str(sum(int(part4Blist[2]), int(part4Clist[2])))) + list(str(sum(int(part4Blist[3]), int(part4Clist[3]))))
    
            print("Part-4 BC list                                   :", part4BClist, file=f)
    
            part4AClist = list(str(sum(int(part4AClist[0]), int(part4AClist[1])))) + list(str(sum(int(part4AClist[2]), int(part4AClist[3]))))
    
            print("Part-4 AC list SUM                               :", part4AClist, file=f)
    
            part4BClist = list(str(sum(int(part4BClist[0]), int(part4BClist[1])))) + list(str(sum(int(part4BClist[2]), int(part4BClist[3]))))
    
            print("Part-4 BC list SUM                               :", part4BClist, file=f)
    
            part4FinalList = part4AClist + part4BClist
    
            print("Part-4 Final list                                :",part4FinalList , file=f)
    
            print("=============================", file=f)
    
            tC = sum(int(a2res[0]), int(TotalC[0]))
            tC1 = sum(int(a2res[1]) , int(TotalC[1]))
                
            listC = [ str(tC), str(tC1) ]
    
            DestinyList = listC
    
            DestinyCount = sum(int(str(tC)), int(str(tC1)))
    
            print("DestinyCount and DestinyList                     :", DestinyCount, DestinyList, file=f)
    
            matrixC = listC + listC
    
            matrixCtotal = sum4(int(matrixC[0]) , int(matrixC[1]), int(matrixC[2]), int(matrixC[3]))
    
            print ("Matrix 3 Final Calculation                      : ", listC, matrixC, matrixCtotal, file=f)
    
            matrix3WinA, matrix3WinB, matrix3LossA, matrix3LossB = getWLTable(matrixCtotal, matrixCtotal)
            Matrix3rA = sum(matrix3WinA, matrix3LossA)
            Matrix3rB = sum(matrix3WinB , matrix3LossB)
            Matrix3cA = sum(matrix3WinA, matrix3WinB)
            Matrix3cB = sum(matrix3LossA , matrix3LossB)
    
            print ("======== Matrix C Begin =================", file=f)
            print ("{:<8} {:<15} {:<10}".format('Person','Win','Loss', "="), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format('------','--','----', ""), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( matrixCtotal, matrix3WinA, matrix3LossA, Matrix3rA), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( matrixCtotal, matrix3WinB, matrix3LossB, Matrix3rB), file=f)
            print ("{:<8} {:<15} {:<10}".format('','--','----'), file=f)
            print ("{:<8} {:<15} {:<10}".format( " ", Matrix3cA, Matrix3cB), file=f)
            print ("======== Matrix C End =================", file=f)
    
            matrix3List = list(str(Matrix3cA)) + list(str(Matrix3rA)) + list(str(Matrix3rB)) + list(str(Matrix3cB))
    
            listA = listA + [ str(tC), str(tC1)]
            listB = listB + [ str(tC), str(tC1)]
    
            tA = sum4(int(listA[0]) , int(listA[1]), int(listA[2]), int(listA[3]))
            totalCountA = tA
    
            tB = sum4(int(listB[0]) , int(listB[1]) , int(listB[2]) , int(listB[3]))
            totalCountB = tB
    
            print("===========================================================", file=f)
            print ("List of A                                       :", listA, file=f)
            print ("List of B                                       :", listB, file=f)
            print ("Total Count for A and B                         :", totalCountA, totalCountB, file=f)
            A,B = totalCountA,totalCountB
            BattleFieldValue = list(str(get_battlefield_value(A,B)))
            print(f"Battle Field Values for {A,B} or {B,A} is       : {BattleFieldValue}", file=f)
            WinMaxValue = list(str(get_win_max_value(A,B)))
            WinMaxValue = ['0'] + WinMaxValue if len(WinMaxValue)<4 else WinMaxValue
            print(f"Win MAX Values for {A,B} or {B,A} is            : {WinMaxValue}", file=f)
            setValues = list(str(get_set_value(A,B)))
            print(f"SET Values for {A,B} or {B,A} is                : {setValues}", file=f)
            print ("==========================================================", file=f)
    
            Plus2A = sum(totalCountA, 2)
            print("Plus2A                                           :", Plus2A, file=f)
            Minus2A = subtract(totalCountA, 2)
            print("Minus2A                                          :", Minus2A, file=f)
            GetxA = getXvalue(sum(sum(Plus2A, Minus2A), totalCountA), totalCountA)
            print("GetxA                                            :", GetxA, file=f)
            Apply2Acount = sum4(Plus2A, Minus2A, totalCountA, GetxA)
            print("Apply2Acount                                     :", Apply2Acount, file=f)
            newA = list(str(Plus2A)) + list(str(Minus2A)) + list(str(totalCountA)) + list(str(GetxA))
            print("newA                                             :", newA, file=f)
    
            Plus2B = sum(totalCountB, 2)
            print("Plus2B                                           :", Plus2B, file=f)
            Minus2B = subtract(totalCountB, 2)
            print("Minus2B                                          :", Minus2B, file=f)
            GetxB = getXvalue(sum(sum(Plus2B, Minus2B), totalCountB), totalCountB)
            print("GetxB                                            :", GetxB, file=f)
            Apply2Bcount = sum4(Plus2B, Minus2B, totalCountB, GetxB)
            print("Apply2Bcount                                     :", Apply2Bcount, file=f)
            newB = list(str(Plus2B)) + list(str(Minus2B)) + list(str(totalCountB)) + list(str(GetxB))
            print("newB                                             :", newB, file=f)
    
            print("Find P ", DestinyCount, DestinyList, newA, file=f)
            p = applyMatrix3Formula1(DestinyCount, DestinyList, newA)
            if len(p) == 0:
                p = applyMatrix3Formula2(DestinyList, newA)
            print("P value after Formula                            :", p, file=f)
            totalp = sum(int(p[2]), int(p[3]))
            print("Total P value.                                   :", totalp, file=f)
    
            print("Find q", DestinyCount, DestinyList, newB, file=f)
            q = applyMatrix3Formula1(DestinyCount, DestinyList, newB)
            if len(q) == 0:
                q = applyMatrix3Formula2(DestinyList, newB)
            print("Q value after Formula                            :", q, file=f)
            totalq = sum(int(q[2]), int(q[3]))
            print("total Q value                                    :", totalq, file=f)
    
            new2 = DestinyList + list(str(totalp)) + list(str(totalq))
    
            print("Part-3 Common P and Q Value                      :", new2, file=f)
    
            Plus1A = sum(int(p[2]), int(p[3])) + 1
            if Plus1A > 9:
                Plus1A = Plus1A - 9
    
            print("Plus1A                                           :", Plus1A, file=f)
    
            Minus1A = sum(int(p[2]), int(p[3])) - 1
            if Minus1A <= 0:
                Minus1A = 9 + Minus1A
    
            print("Minus1A                                          :", Minus1A, file=f)
    
            R = DestinyList + list(str(Plus1A)) + list(str(Minus1A))
    
            print("Part-3 R value                                   :", R, file=f)
    
            R1 = sum(Plus1A , Minus1A)
    
            print("Part-3 R Count                                   :", R1, file=f)
    
            Plus1B = sum(int(q[2]), int(q[3])) + 1
            if Plus1B > 9:
                Plus1A = Plus1B - 9
    
            print("Plus1B                                           :", Plus1B, file=f)
            Minus1B = sum(int(q[2]), int(q[3])) - 1
            if Minus1B <= 0:
                Minus1B = 9 + Minus1B
            print("Minus1B                                          :", Minus1B, file=f)
    
            S = DestinyList + list(str(Plus1B)) + list(str(Minus1B))
    
            print("Part-3 S value:", S, file=f)
    
            S1 = sum(Plus1B, Minus1B)
    
            print("Part-3 S count                                   : ", S1, file=f)
    
            T = DestinyList + list(str(R1)) + list(str(S1))
    
            part3FinalList = T
    
            print("Part-3 Final value                               :", T, file=f)
    
            wA, wB, lA, lB = getWLTable(tA, tB)
    
            #wA = tA - 1
            #if wA == 0:
            #  wA = 9
            #lA = tA + 1
            #if lA == 10:
            #   lA = 1
    
            #wB = tB - 1
            #if wB == 0:
            #   wB = 9
            #lB = tB + 1
            #if lB == 10:
            #   lB = 1
    
            rA = sum(wA, lA)
            rB = sum(wB , lB)
            cA = sum(wA, wB)
            cB = sum(lA , lB)
    
            print ("======== Combined Matrix Begin =================", file=f)
            print ("{:<8} {:<15} {:<10}".format('Person','Win','Loss', "="), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format('------','--','----', ""), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( tA, wA, lA, rA), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( tB, wB, lB, rB), file=f)
            print ("{:<8} {:<15} {:<10}".format('','--','----'), file=f)
            print ("{:<8} {:<15} {:<10}".format( " ", cA, cB), file=f)
            print ("======== Combined Matrix End =================", file=f)
    
            print ("======== Part-6 Begin =================", file=f)
    
            CombinedMatrixList = list(str(cA)) + list(str(cB)) + list(str(rA)) + list(str(rB))
    
            cAcB = sum(cA, cB)
            print("cAcB                                             :", cAcB, file=f)
            p6step4Column = list(str(cA)) + list(str(cAcB)) + list(str(cB)) + list(str(cAcB))
            print("p6step4Column                                    :", p6step4Column, file=f)
            rArB = sum(rA, rB)
            print("rArB                                             :", rArB, file=f)
            p6step4Row = list(str(rA)) + list(str(rArB)) + list(str(rB)) + list(str(rArB))
            print("p6step4Row                                       :", p6step4Row, file=f)
    
            p6TotalB = list(str(sum(int(p6step4Column[0]), int(p6step4Row[0])))) +  list(str(sum(int(p6step4Column[1]), int(p6step4Row[1])))) + list(str(sum(int(p6step4Column[2]), int(p6step4Row[2])))) + list(str(sum(int(p6step4Column[3]), int(p6step4Row[3]))))
            print("p6TotalB                                         :", p6TotalB, file=f)
    
            p6c = int(str(cA)+str(cB))
            p6r = int(str(rB)+str(rA))
    
            print("p6c                                              :", p6c, file=f)
            print("p6r                                              :", p6r, file=f)
    
            if p6c < p6r:
                p6 = p6r - p6c
            else:
                p6 = p6c - p6r
            if p6 == 0:
                p6 = 9
            if p6 < 10:
                p6str=str(0)+str(p6)
            else:
                p6str=str(p6)
                
            p6list = list(p6str)
            print("p6list 14-23 Result                              :", p6list, file=f)
    
            p6stepA = list(str(cA)) + p6list + list(str(cB))
            p6stepB = list(str(rB)) + p6list + list(str(rA))
    
            print("p6stepA                                          ", p6stepA, file=f)
            print("p6stepB                                          ", p6stepB, file=f)
    
            p6TotalA = list(str(sum(int(p6stepA[0]), int(p6stepB[0])))) +  list(str(sum(int(p6stepA[1]), int(p6stepB[1])))) + list(str(sum(int(p6stepA[2]), int(p6stepB[2])))) + list(str(sum(int(p6stepA[3]), int(p6stepB[3]))))
            print("Part-6 Total A                                   :", p6TotalA, file=f)
            print("Part-6 Total B                                   :", p6TotalB, file=f)
    
            Part6Finalvalue = list(str(sum(int(p6TotalA[0]), int(p6TotalB[0])))) +  list(str(sum(int(p6TotalA[1]), int(p6TotalB[1])))) + list(str(sum(int(p6TotalA[2]), int(p6TotalB[2])))) + list(str(sum(int(p6TotalA[3]), int(p6TotalB[3]))))
            print("Part-6 Final Result                              :", Part6Finalvalue, file=f)
            print ("======== Part-6 End =================", file=f)
    
            print("Matrix1 List                                     :", matrix1List, file=f)
            print("Matrix2 List                                     :", matrix2List, file=f)
            print("Matrix3 List                                     :", matrix3List, file=f)
            print("Combined Matrix List                             :", CombinedMatrixList, file=f)
    
            AllMatrix = list(str(sum4(int(matrix1List[0]), int(matrix2List[0]), int(matrix3List[0]), int(CombinedMatrixList[0])))) + list(str(sum4(int(matrix1List[1]), int(matrix2List[1]), int(matrix3List[1]), int(CombinedMatrixList[1])))) + list(str(sum4(int(matrix1List[2]), int(matrix2List[2]), int(matrix3List[2]), int(CombinedMatrixList[2])))) + list(str(sum4(int(matrix1List[3]), int(matrix2List[3]), int(matrix3List[3]), int(CombinedMatrixList[3]))))
    
            print("All Matrix Calculation                           :", AllMatrix, file=f)
    
            predefinedint = [0000, 8201, 8311, 8421, 8531, 8641, 8751, 8861, 8971, 8181]
            sevenHit = 0 
            twoHit = 0
    
            convertA = list(str(predefinedint[totalCountA]))
            convertB = list(str(predefinedint[totalCountB]))
    
            #print("Convert Person A total count to 1-8 Formula", convertA, file=f)
            #print("Convert Person B total count to 1-8 Formula", convertB, file=f)
    
            sevenHit = 0 
            twoHit = 0
    
            fOne = sum(int(convertA[0]) , int(convertB[0]))
    
            sevenHit, twoHit, fOne = is72(sevenHit, twoHit, fOne)
    
            fTwo = sum(int(convertA[1]) , int(convertB[1]))
    
            sevenHit, twoHit, fTwo = is72(sevenHit, twoHit, fTwo)
    
            fThree = sum(int(convertA[2]) , int(convertB[2]))
    
            sevenHit, twoHit, fThree = is72(sevenHit, twoHit, fThree)
    
            fFour = sum(int(convertA[3]) , int(convertB[3]))
    
            sevenHit, twoHit, fFour = is72(sevenHit, twoHit,fFour)
    
    
            if sevenHit == 0 or twoHit == 0:
                print("SOMETHING WRONGGGG>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", file=f)
                exit(1)
    
    
            personResult = []
    
            personResult = get18Formula(personResult, fOne, fTwo, fThree, fFour)
    
    
            #print("1-8 Formula Conversion of Total Count of Person A and B: ", personResult, file=f)
    
            sevenHit = 0
            twoHit = 0
    
            convertA = list(str(predefinedint[wA]))
            convertB = list(str(predefinedint[lA]))
    
            #print('\nConvert Person A Win and Loss information to 1-8 Formula:', file=f)
            #print("Win Number, Converted Number:", wA, convertA, file=f)
            #print("Loss Number, Converted Number:", lA, convertB, file=f)
    
            fOne = sum(int(convertA[0]) , int(convertB[0]))
    
            sevenHit, twoHit, fOne = is72(sevenHit, twoHit, fOne)
    
            fTwo = sum(int(convertA[1]) , int(convertB[1]))
    
            sevenHit, twoHit, fTwo = is72(sevenHit, twoHit, fTwo)
    
            fThree = sum(int(convertA[2]) , int(convertB[2]))
    
            sevenHit, twoHit, fThree = is72(sevenHit, twoHit, fThree)
    
            fFour = sum(int(convertA[3]) , int(convertB[3]))
    
            sevenHit, twoHit, fFour = is72(sevenHit, twoHit,fFour)
    
            if sevenHit == 0 or twoHit == 0:
                print("SOMETHING WRONGGGG>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", file=f)
                exit (1)
    
            personAresult = []
    
            personAresult = get18Formula(personAresult, fOne, fTwo, fThree, fFour)
    
            #print("1-8 Formula Conversion of Person A Win and Loss: ", personAresult, file=f)
    
            sevenHit = 0
            twoHit = 0
    
            convertA = list(str(predefinedint[wB]))
            convertB = list(str(predefinedint[lB]))
    
            #print('\nConvert Person B Win and Loss information to 1-8 Formula:', file=f)
            #print("Win Number, Converted Number:", wB, convertA, file=f)
            #print("Loss Number, Converted Number:", lB, convertB, file=f)
    
            fOne = sum(int(convertA[0]) , int(convertB[0]))
    
            sevenHit, twoHit, fOne = is72(sevenHit, twoHit, fOne)
    
            fTwo = sum(int(convertA[1]) , int(convertB[1]))
    
            sevenHit, twoHit, fTwo = is72(sevenHit, twoHit, fTwo)
    
            fThree = sum(int(convertA[2]) , int(convertB[2]))
    
            sevenHit, twoHit, fThree = is72(sevenHit, twoHit, fThree)
    
            fFour = sum(int(convertA[3]) , int(convertB[3]))
    
            sevenHit, twoHit, fFour = is72(sevenHit, twoHit,fFour)
    
            if sevenHit == 0 or twoHit == 0:
                print("SOMETHING WRONGGGG>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", file=f)
                exit (1)
    
            personBresult = []
    
            personBresult = get18Formula(personBresult, fOne, fTwo, fThree, fFour)
    
            #print("1-8 Formula Conversion of Person B Win and Loss: ", personBresult, file=f)
    
            t1 = sum(int(personAresult[0]) , int(personBresult[0]))
                
            t2 = sum(int(personAresult[1]) , int(personBresult[1]))
    
            fList = list(str(t1)) + list(str(t2)) + personResult
            #print("\nFinal Sum of Person A and B", fList, file=f)
    
            print("Final Column and Row Values                    :", cA, cB, rA, rB, file=f)
    
            myA1 = getXvalue(cA, totalCountA)
            myA2 = getXvalue(cA, totalCountB)
    
            sumA = list(str(sum(cA, cA)) + str(sum(myA1, myA2)) + str(totalCountA) + str(totalCountB))
    
            print("sumA                                             :", sumA, file=f)
    
            myB1 = getXvalue(cB, totalCountA)
            myB2 = getXvalue(cB, totalCountB)
    
            sumB = list(str(sum(cB, cB)) + str(sum(myB1, myB2)) + str(totalCountA) + str(totalCountB))
    
            print("sumB                                             :", sumB, file=f)
    
    
            myC1 = getXvalue(rA, totalCountA)
            myC2 = getXvalue(rA, totalCountB)
    
            sumC = list(str(sum(rA, rA)) + str(sum(myC1, myC2)) + str(totalCountA) + str(totalCountB))
    
            print("sumC                                             :", sumC, file=f)
    
    
            myD1 = getXvalue(rB, totalCountA)
            myD2 = getXvalue(rB, totalCountB)
    
            sumD = list(str(sum(rB, rB)) + str(sum(myD1, myD2)) + str(totalCountA) + str(totalCountB))
    
            print("sumD                                             :", sumD, file=f)
    
    
            totalSumA = sum4(int(sumA[0]), int(sumB[0]), int(sumC[0]), int(sumD[0]))
            totalSumB = sum4(int(sumA[1]), int(sumB[1]), int(sumC[1]), int(sumD[1]))
            totalSumC = sum4(int(sumA[2]), int(sumB[2]), int(sumC[2]), int(sumD[2]))
            totalSumD = sum4(int(sumA[3]), int(sumB[3]), int(sumC[3]), int(sumD[3]))
    
            print("Final Result                                     :", totalSumA, totalSumB, totalSumC, totalSumD, file=f)
    
            firsthalf   = sum(totalSumA, totalSumB)
            secondhalf  = sum(totalSumC, totalSumD)
    
            Part1PredictionList = list(str(totalSumA)) + list(str(totalSumB)) + list(str(firsthalf)) + list(str(secondhalf))
            Part2PredictionList =   list(str(sum(int(AllMatrix[0]), int(Part1PredictionList[0])))) + list(str(sum(int(AllMatrix[1]), int(Part1PredictionList[1])))) + list(str(sum(int(AllMatrix[2]), int(Part1PredictionList[2])))) + list(str(sum(int(AllMatrix[3]), int(Part1PredictionList[3]))))
    
            CC = list(str(DestinyCountLast2) + str(PlayerA))
            DD = list(str(DestinyCountLast2) + str(PlayerB))
            EE = list(str(PlayerA) + str(PlayerB))
            print("Total A again and CC                             :", TotalA, CC, file=f)
            print("Total B again and DD                             :", TotalB, DD, file=f)
            print("Total C again and EE                             :", TotalC, EE, file=f)
    
            print("Find xxxx for (CC,DD) and Total A and B          :", CC, DD, TotalA, TotalB, file=f)
            CCCCa = str(getXvalue(int(CC[0]), int(TotalA[0])))
            CCCCb = str(getXvalue(int(CC[1]), int(TotalA[1])))
            CCCCc = str(getXvalue(int(DD[0]), int(TotalB[0])))
            CCCCd = str(getXvalue(int(DD[1]), int(TotalB[1])))
    
            CCCCabcdlist = list(CCCCa) + list(CCCCb) + list(CCCCc) + list(CCCCd)
            print("CCCCabcdlist                                     :", CCCCabcdlist, file=f)
    
            print("Find xxxx for Total (A and B) and CCCCabcdlist   :", TotalA, TotalB, CCCCabcdlist, file=f)
            CCCCp = str(getXvalue(int(TotalA[0]), int(CCCCabcdlist[0])))
            CCCCq = str(getXvalue(int(TotalA[1]), int(CCCCabcdlist[1])))
            CCCCr = str(getXvalue(int(TotalB[0]), int(CCCCabcdlist[2])))
            CCCCs = str(getXvalue(int(TotalB[1]), int(CCCCabcdlist[3])))
    
            CCCCpqrslist = list(CCCCp) + list(CCCCq) + list(CCCCr) + list(CCCCs)
            print("CCCCpqrslist                                     :", CCCCpqrslist, file=f)
    
            TT = list(str(sum(int(CCCCabcdlist[0]), int(CCCCabcdlist[1])))) + list(str(sum(int(CCCCabcdlist[2]), int(CCCCabcdlist[3])))) + list(str(sum4(int(TotalA[0]), int(TotalA[1]), int(TotalB[0]), int(TotalB[1])))) + list(str(sum4(int(CCCCpqrslist[0]), int(CCCCpqrslist[1]), int(CCCCpqrslist[2]), int(CCCCpqrslist[3]))))
            print("TT Value                                         :", TT, file=f)
    
    
            print("Find xxxx for (CC,DD) and Total C                :", CC, DD, TotalC, TotalC, file=f)
            CCCC1 = str(getXvalue(int(CC[0]), int(TotalC[0])))
            CCCC2 = str(getXvalue(int(CC[1]), int(TotalC[1])))
            CCCC3 = str(getXvalue(int(DD[0]), int(TotalC[0])))
            CCCC4 = str(getXvalue(int(DD[1]), int(TotalC[1])))
    
            CCCC1234list = list(CCCC1) + list(CCCC2) + list(CCCC3) + list(CCCC4)
            print("CCCC1234list                                     :", CCCC1234list, file=f)
    
            print("Find xxxx for Total C and CCCC1234list           :", TotalC, TotalC, CCCC1234list, file=f)
            CCCC5 = str(getXvalue(int(TotalC[0]), int(CCCC1234list[0])))
            CCCC6 = str(getXvalue(int(TotalC[1]), int(CCCC1234list[1])))
            CCCC7 = str(getXvalue(int(TotalC[0]), int(CCCC1234list[2])))
            CCCC8 = str(getXvalue(int(TotalC[1]), int(CCCC1234list[3])))
    
            CCCC5678list = list(CCCC5) + list(CCCC6) + list(CCCC7) + list(CCCC8)
            print("CCCC5678list                                     :", CCCC5678list, file=f)
    
            UU = list(str(sum(int(CCCC1234list[0]), int(CCCC1234list[1])))) + list(str(sum(int(CCCC1234list[2]), int(CCCC1234list[3])))) + list(str(sum4(int(TotalC[0]), int(TotalC[1]), int(TotalC[0]), int(TotalC[1])))) + list(str(sum4(int(CCCC5678list[0]), int(CCCC5678list[1]), int(CCCC5678list[2]), int(CCCC5678list[3]))))
            print("UU Value                                         :", UU, file=f)
    
            YY = list(str(sum(int(TT[0]), int(UU[0])))) + list(str(sum(int(TT[1]), int(UU[1])))) + list(str(sum(int(TT[2]), int(UU[2])))) + list(str(sum(int(TT[3]), int(UU[3]))))
            print("TT + UU Value = YY                               :", YY, file=f)
    
    
            print("Find xx for TotalA(CC) with TotalC               :", CC, TotalC, file=f)
            CCa = str(getXvalue(int(CC[0]), int(TotalC[0])))
            CCb = str(getXvalue(int(CC[1]), int(TotalC[1])))
            CCablist = list(CCa) + list(CCb)
            print("CCablist                                         :", CCablist, file=f)
    
            print("Find xx for TotalC with CC                       :", TotalC, CCablist, file=f)
            CCx = str(getXvalue(int(TotalC[0]), int(CCablist[0])))
            CCy = str(getXvalue(int(TotalC[1]), int(CCablist[1])))
            CCxylist = list(CCx) + list(CCy)
            print("CCxylist                                         :", CCxylist, file=f)
    
            RR = CCablist + list(str(sum(int(TotalC[0]), int(TotalC[1])))) + list(str(sum(int(CCxylist[0]), int(CCxylist[1]))))
    
            print("Find xx for TotalB(DD) with TotalC               :", DD, TotalC, file=f)
            DDa = str(getXvalue(int(DD[0]), int(TotalC[0])))
            DDb = str(getXvalue(int(DD[1]), int(TotalC[1])))
            DDablist = list(DDa) + list(DDb)
    
            print("Find xx for TotalC with DD                       :", TotalC, DDablist, file=f)
            DDx = str(getXvalue(int(TotalC[0]), int(DDablist[0])))
            DDy = str(getXvalue(int(TotalC[1]), int(DDablist[1])))
            DDxylist = list(DDx) + list(DDy)
            print("DDxylist                                         :", DDxylist, file=f)
    
            QQ = DDablist + list(str(sum(int(TotalC[0]), int(TotalC[1])))) + list(str(sum(int(DDxylist[0]), int(DDxylist[1]))))
    
            print("Find xx for TotalAB(EE) with TotalC              :", EE, TotalC, file=f)
            EEa = str(getXvalue(int(EE[0]), int(TotalC[0])))
            EEb = str(getXvalue(int(EE[1]), int(TotalC[1])))
            EEablist = list(EEa) + list(EEb)
    
            print("Find xx for TotalC with EE                       :", TotalC, EEablist, file=f)
            EEx = str(getXvalue(int(TotalC[0]), int(EEablist[0])))
            EEy = str(getXvalue(int(TotalC[1]), int(EEablist[1])))
            EExylist = list(EEx) + list(EEy)
            print("EExylist                                         :", EExylist, file=f)
    
            PP = EEablist + list(str(sum(int(TotalC[0]), int(TotalC[1])))) + list(str(sum(int(EExylist[0]), int(EExylist[1]))))
    
            SS = list(str(sum3(int(PP[0]), int(QQ[0]), int(RR[0])))) + list(str(sum3(int(PP[1]), int(QQ[1]), int(RR[1])))) + list(str(sum3(int(PP[2]), int(QQ[2]), int(RR[2])))) + list(str(sum3(int(PP[3]), int(QQ[3]), int(RR[3]))))
            part5SS = SS
            print("Part-5 step1 PP results                          :", PP, file=f)
            print("Part-5 step1 QQ results                          :", QQ, file=f)
            print("Part-5 step1 RR results                          :", RR, file=f)
            print("Part-5 step1 PP+QQ+RR=SS results                 :", SS, file=f)
        
            print("Find xx for TotalA(CC) with TotalB               :", CC, TotalB, file=f)
            CCCa = str(getXvalue(int(CC[0]), int(TotalB[0])))
            CCCb = str(getXvalue(int(CC[1]), int(TotalB[1])))
            CCCablist = list(CCCa) + list(CCCb)
    
            print("Find xx for TotalB with CC                       :", TotalB, CCCablist, file=f)
            CCCx = str(getXvalue(int(TotalB[0]), int(CCCablist[0])))
            CCCy = str(getXvalue(int(TotalB[1]), int(CCCablist[1])))
            CCCxylist = list(CCCx) + list(CCCy)
            print("CCCxylist                                        :", CCCxylist, file=f)
    
            VV = CCCablist + list(str(sum(int(TotalB[0]), int(TotalB[1])))) + list(str(sum(int(CCCxylist[0]), int(CCCxylist[1]))))
    
            print("Part-5 VV results                                :", VV, file=f)
    
            print("Find xx for TotalB(DD) with TotalA               :", DD, TotalA, file=f)
            DDDa = str(getXvalue(int(DD[0]), int(TotalA[0])))
            DDDb = str(getXvalue(int(DD[1]), int(TotalA[1])))
            DDDablist = list(DDDa) + list(DDDb)
    
            print("Find xx for TotalA with DD                       :", TotalA, DDablist, file=f)
            DDDx = str(getXvalue(int(TotalA[0]), int(DDDablist[0])))
            DDDy = str(getXvalue(int(TotalA[1]), int(DDDablist[1])))
            DDDxylist = list(DDDx) + list(DDDy)
            print("DDDxylist                                        :", DDDxylist, file=f)
    
            WW = DDDablist + list(str(sum(int(TotalA[0]), int(TotalA[1])))) + list(str(sum(int(DDDxylist[0]), int(DDDxylist[1]))))
    
            print("Part-5 WW results                                :", WW, file=f)
    
            XX = list(str(sum3(int(PP[0]), int(VV[0]), int(WW[0])))) + list(str(sum3(int(PP[1]), int(VV[1]), int(WW[1])))) + list(str(sum3(int(PP[2]), int(VV[2]), int(WW[2])))) + list(str(sum3(int(PP[3]), int(VV[3]), int(WW[3]))))
    
            print("Part-5 XX results                                :", XX, file=f)
    
            ZZ = list(str(sum(int(XX[0]), int(SS[0])))) + list(str(sum(int(XX[1]), int(SS[1])))) + list(str(sum(int(XX[2]), int(SS[2])))) + list(str(sum(int(XX[3]), int(SS[3]))))
    
            print("Part-5 ZZ results                                :", ZZ, file=f)
            print("Part-5 YY results                                :", YY, file=f)
    
            Part5Finalvalue = list(str(sum(int(ZZ[0]), int(YY[0])))) + list(str(sum(int(ZZ[1]), int(YY[1])))) + list(str(sum(int(ZZ[2]), int(YY[2])))) + list(str(sum(int(ZZ[3]), int(YY[3]))))
    
            Part7List = list(str(sum(rA, cA))) + list(str(sum(rA, cB))) + list(str(sum(rB, cB))) + list(str(sum(rB, cA)))
            print("===========================================================", file=f)
            print("Part-1  Result                                   :", Part1PredictionList, file=f)
            print("Part-2  Result                                   :", Part2PredictionList, file=f)
            print("Part-3  Result                                   :", part3FinalList, file=f)
            print("Part-4  Result                                   :", part4FinalList , file=f)
            print("Part-5  Results                                  :", Part5Finalvalue, file=f)
            print("Part-6  Results                                  :", Part6Finalvalue, file=f)
            print("Part-7 Results                                   :", Part7List, file=f)
    
            U1 = list(str(sum4(int(Part1PredictionList[0]), int(Part2PredictionList[0]), int(part3FinalList[0]), int(part4FinalList[0])))) + list(str(sum4(int(Part1PredictionList[1]), int(Part2PredictionList[1]), int(part3FinalList[1]), int(part4FinalList[1])))) + list(str(sum4(int(Part1PredictionList[2]), int(Part2PredictionList[2]), int(part3FinalList[2]), int(part4FinalList[2])))) + list(str(sum4(int(Part1PredictionList[3]), int(Part2PredictionList[3]), int(part3FinalList[3]), int(part4FinalList[3])))) 
    
            U2 = list(str(sum(int(Part5Finalvalue[0]), int(Part6Finalvalue[0])))) + list(str(sum(int(Part5Finalvalue[1]), int(Part6Finalvalue[1])))) + list(str(sum(int(Part5Finalvalue[2]), int(Part6Finalvalue[2])))) + list(str(sum(int(Part5Finalvalue[3]), int(Part6Finalvalue[3]))))
    
            AllSixSum = list(str(sum(int(U1[0]), int(U2[0])))) + list(str(sum(int(U1[1]), int(U2[1])))) + list(str(sum(int(U1[2]), int(U2[2])))) + list(str(sum(int(U1[3]), int(U2[3]))))
    
            UltimateResult = list(str(sum(int(Part7List[0]), int(AllSixSum[0])))) + list(str(sum(int(Part7List[1]), int(AllSixSum[1])))) + list(str(sum(int(Part7List[2]), int(AllSixSum[2])))) + list(str(sum(int(Part7List[3]), int(AllSixSum[3]))))
    
            r1 = wA * 5
            if r1 < 10:
                Rnum1 = int(r1)
            else:
                r1list = convert2list(str(r1))
                Rnum1 = sum(int(r1list[0]), int(r1list[1]))
    
            r1 = lA * 5
            if r1 < 10:
                Rnum2 = int(r1)
            else:
                r1list = convert2list(str(r1))
                Rnum2 = sum(int(r1list[0]), int(r1list[1]))
    
            r1 = wB * 5
            if r1 < 10:
                Rnum3 = int(r1)
            else:
                r1list = convert2list(str(r1))
                Rnum3 = sum(int(r1list[0]), int(r1list[1]))
                
            r1 = lB * 5
            if r1 < 10:
                Rnum4 = int(r1)
            else:
                r1list = convert2list(str(r1))
                Rnum4 = sum(int(r1list[0]), int(r1list[1]))
    
            myr1 = getXvalue(cA, Rnum1)
            myr2 = getXvalue(cB, Rnum1)
            myr1list = list(str(cA)) + list(str(myr1)) + list(str(cB)) + list(str(myr2))
    
            myr1 = getXvalue(cA, Rnum2)
            myr2 = getXvalue(cB, Rnum2)
            myr2list = list(str(cA)) + list(str(myr1)) + list(str(cB)) + list(str(myr2))
    
            myr1 = getXvalue(cA, Rnum3)
            myr2 = getXvalue(cB, Rnum3)
            myr3list = list(str(cA)) + list(str(myr1)) + list(str(cB)) + list(str(myr2))
    
            myr1 = getXvalue(cA, Rnum4)
            myr2 = getXvalue(cB, Rnum4)
            myr4list = list(str(cA)) + list(str(myr1)) + list(str(cB)) + list(str(myr2))
    
            my8A = list(str(sum4(int(myr1list[0]), int(myr2list[0]), int(myr3list[0]), int(myr4list[0])))) + list(str(sum4(int(myr1list[1]), int(myr2list[1]), int(myr3list[1]), int(myr4list[1])))) + list(str(sum4(int(myr1list[2]), int(myr2list[2]), int(myr3list[2]), int(myr4list[2])))) + list(str(sum4(int(myr1list[3]), int(myr2list[3]), int(myr3list[3]), int(myr4list[3])))) 
            #print("My Part-8 Results A                              :", my8A, file=f)
            myr1 = getXvalue(rA, Rnum1)
            myr2 = getXvalue(rB, Rnum1)
            myr1list = list(str(rA)) + list(str(myr1)) + list(str(rB)) + list(str(myr2))
    
            myr1 = getXvalue(rA, Rnum2)
            myr2 = getXvalue(rB, Rnum2)
            myr2list = list(str(rA)) + list(str(myr1)) + list(str(rB)) + list(str(myr2))
    
            myr1 = getXvalue(rA, Rnum3)
            myr2 = getXvalue(rB, Rnum3)
            myr3list = list(str(rA)) + list(str(myr1)) + list(str(rB)) + list(str(myr2))
    
            myr1 = getXvalue(rA, Rnum4)
            myr2 = getXvalue(rB, Rnum4)
            myr4list = list(str(rA)) + list(str(myr1)) + list(str(rB)) + list(str(myr2))
    
            my8B = list(str(sum4(int(myr1list[0]), int(myr2list[0]), int(myr3list[0]), int(myr4list[0])))) + list(str(sum4(int(myr1list[1]), int(myr2list[1]), int(myr3list[1]), int(myr4list[1])))) + list(str(sum4(int(myr1list[2]), int(myr2list[2]), int(myr3list[2]), int(myr4list[2])))) + list(str(sum4(int(myr1list[3]), int(myr2list[3]), int(myr3list[3]), int(myr4list[3])))) 
            #print("My Part-8 Results B                              :", my8B, file=f)
    
            part8Result = list(str(sum(int(my8A[0]), int(my8B[0])))) + list(str(sum(int(my8A[1]), int(my8B[1])))) + list(str(sum(int(my8A[2]), int(my8B[2])))) + list(str(sum(int(my8A[3]), int(my8B[3]))))
    
            TableAP = list(str(cA)) + list(str(cB))
            TableAQ = list(str(cA)) + list(str(cB)) + list(str(rA)) + list(str(rB))
            TableAPQ = TableAP + TableAQ
            TableAT = list(TableAPQ[0]) + list(TableAPQ[1]) + list(TableAPQ[2]) + list(str(sum3(int(str(TableAPQ[3])), int(str(TableAPQ[4])), int(str(TableAPQ[5])))))
            #print("TableAT                                          :", TableAT, file=f)
    
            TableAR = list(str(rA)) + list(str(rB))
            TableAS = list(str(rA)) + list(str(rB)) + list(str(cA)) + list(str(cB))
            TableARS = TableAR + TableAS
            TableAU = list(TableARS[0]) + list(TableARS[1]) + list(TableARS[2]) + list(str(sum3(int(str(TableARS[3])), int(str(TableARS[4])), int(str(TableARS[5])))))
            #print("TableAU                                          :", TableAU, file=f)
            TableAV = list(str(sum(int(TableAT[0]), int(TableAU[0])))) + list(str(sum(int(TableAT[1]), int(TableAU[1])))) + list(str(sum(int(TableAT[2]), int(TableAU[2])))) + list(str(sum(int(TableAT[3]), int(TableAU[3]))))
            #print("TableAV                                          :", TableAV, file=f)
            print("========================", file=f)
            TableAK = list(str(cB)) + list(str(cA))
            TableAL = list(str(cB)) + list(str(cA)) + list(str(rA)) + list(str(rB))
            TableAKL = TableAK + TableAL
            TableAW = list(TableAKL[0]) + list(TableAKL[1]) + list(TableAKL[2]) + list(str(sum3(int(str(TableAKL[3])), int(str(TableAKL[4])), int(str(TableAKL[5])))))
            #print("TableAW                                          :", TableAW, file=f)
    
            TableAM = list(str(rB)) + list(str(rA))
            TableAN = list(str(rB)) + list(str(rA)) + list(str(cB)) + list(str(cA))
            TableAMN = TableAM + TableAN
            TableAX = list(TableAMN[0]) + list(TableAMN[1]) + list(TableAMN[2]) + list(str(sum3(int(str(TableAMN[3])), int(str(TableAMN[4])), int(str(TableAMN[5])))))
            #print("TableAX                                          :", TableAX, file=f)
            TableAY = list(str(sum(int(TableAW[0]), int(TableAX[0])))) + list(str(sum(int(TableAW[1]), int(TableAX[1])))) + list(str(sum(int(TableAW[2]), int(TableAX[2])))) + list(str(sum(int(TableAW[3]), int(TableAX[3]))))
            #print("TableAY                                          :", TableAY, file=f)
    
            Part9Result = list(str(sum(int(TableAV[0]), int(TableAY[0])))) + list(str(sum(int(TableAV[1]), int(TableAY[1])))) + list(str(sum(int(TableAV[2]), int(TableAY[2])))) + list(str(sum(int(TableAV[3]), int(TableAY[3]))))
            print("===========================================================", file=f)
            print("AllSix Sum Results                               :", AllSixSum, file=f)
            print("Display Matrix 1                                 :", DisplayMatrix1, file=f)
            print("Display Matrix 2                                 :", DisplayMatrix2, file=f)
            print("Display Matrix 3                                 :", DisplayMatrix3, file=f)
            print ("List of A                                       :", listA, file=f)
            print ("List of B                                       :", listB, file=f)
            print ("Total Count for A and B                         :", totalCountA, totalCountB, file=f)
            print ("======== Combined Matrix Begin =================", file=f)
            print ("{:<8} {:<15} {:<10}".format('Person','Win','Loss', "="), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format('------','--','----', ""), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( tA, wA, lA, rA), file=f)
            print ("{:<8} {:<15} {:<10} {:<10}".format( tB, wB, lB, rB), file=f)
            print ("{:<8} {:<15} {:<10}".format('','--','----'), file=f)
            print ("{:<8} {:<15} {:<10}".format( " ", cA, cB), file=f)
            print ("======== Combined Matrix End =================", file=f)
            print ("==========================================================", file=f)
            print("Sum of Part-1 to 6                               :", UltimateResult, file=f)
            Part1to6 = UltimateResult
            print ("==========================================================", file=f)
            print("Part-8 Results                                   :", part8Result, file=f)
            print("Part-9 Results                                   :", Part9Result, file=f)
    
            TVList = ["9593", "5957" ,"1412" , "6866" , "2321" , "7775",  "3239"  ,"8684" , "4148" , "9593" ]
    
            a2twice = list(a2res[1]) + list(TotalC[1]) + list(a2res[1]) + list(TotalC[1])
            aa1 = list(ares[1]) + list(TotalA[1]) + list(a1res[1]) + list(TotalB[1])
    
            a2aa1total = list(str(sum(int(a2twice[0]), int(aa1[0])))) + list(str(sum(int(a2twice[1]), int(aa1[1])))) + list(str(sum(int(a2twice[2]), int(aa1[2])))) + list(str(sum(int(a2twice[3]), int(aa1[3]))))
    
            print("Matrix 1&2&3                         a1          :", a2aa1total, file=f)
    
            Geta2aaX0 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(a2aa1total[0]))))
            Geta2aaX1 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(a2aa1total[1]))))
            Geta2aaX2 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(a2aa1total[2]))))
            Geta2aaX3 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(a2aa1total[3]))))
    
            print("GetValue with CountA                             :", totalCountA, Geta2aaX0, Geta2aaX1, Geta2aaX2, Geta2aaX3, file=f)
    
    
            Geta2aaY0 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(a2aa1total[0]))))
            Geta2aaY1 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(a2aa1total[1]))))
            Geta2aaY2 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(a2aa1total[2]))))
            Geta2aaY3 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(a2aa1total[3]))))
    
            print("GetValue with CountB                             :", totalCountB, Geta2aaY0, Geta2aaY1, Geta2aaY2, Geta2aaY3, file=f)
    
            XY00 = str(sum(int(Geta2aaX0[0]), int(Geta2aaY0[0])))
            XY01 = str(sum(int(Geta2aaX0[1]), int(Geta2aaY0[1])))
    
            XY10 = str(sum(int(Geta2aaX1[0]), int(Geta2aaY1[0])))
            XY11 = str(sum(int(Geta2aaX1[1]), int(Geta2aaY1[1])))
    
            XY20 = str(sum(int(Geta2aaX2[0]), int(Geta2aaY2[0])))
            XY21 = str(sum(int(Geta2aaX2[1]), int(Geta2aaY2[1])))
    
            XY30 = str(sum(int(Geta2aaX3[0]), int(Geta2aaY3[0])))
            XY31 = str(sum(int(Geta2aaX3[1]), int(Geta2aaY3[1])))
    
            print("Sum GetValue A and B     b1                      :", XY00, XY01, XY10, XY11, XY20, XY21, XY30, XY31, file=f)
    
            XY0 = sum(int(XY00), totalCountA)
            XY1 = sum(int(XY10), totalCountB)
            XY2 = sum(int(XY20), 3)
            XY3 = sum(int(XY30), sum(totalCountA, totalCountB))
    
            print("XY First set with Constant 3         f1          :", XY0, XY1, XY2, XY3, file=f)
    
            GetTV = list(TVList[sum(totalCountA, totalCountB)])
    
            print("TV Value of toalCountA and totalCountB           :", GetTV, file=f)
    
            XY4 = sum(int(XY01), int(GetTV[0]))
            XY5 = sum(int(XY11), int(GetTV[1]))
            XY6 = sum(int(XY21), int(GetTV[2]))
            XY7 = sum(int(XY31), int(GetTV[3]))
    
            print("XY Second set with TV                g1          :", XY4, XY5, XY6, XY7, file=f)
    
            XY8 = list(str(sum(XY0, XY1))) + list(str(sum(XY2, XY3))) + list(str(sum(XY4, XY5))) + list(str(sum(XY6, XY7))) 
    
            print("XY Combination of First and Second set g1 and f1 is h1   :", XY8, file=f)
    
            if sum(rA, rB) == sum(cA, cB):
                XY9 = list(str(rB)) + list(str(cA)) + list(str(cB)) + list(str(rA))
                print("XY9 - 1 from WinLoss Table           i1      :", XY9, file=f)
            elif sum(cA, rA) == sum(cB, rB):
                XY9 = list(str(rA)) + list(str(cB)) + list(str(cA)) + list(str(rB))
                print("XY9 - 2 from WinLoss Table           i1      :", XY9, file=f)
            elif sum(cA, rB) == sum(cB, rA):
                XY9 = list(str(rB)) + list(str(cB)) + list(str(cA)) + list(str(rA))
                print("XY9 - 3 from WinLoss Table           i1      :", XY9, file=f)
            elif sum(cB, rA) == sum(cA, rB):
                XY9 = list(str(rA)) + list(str(cA)) + list(str(cB)) + list(str(rB))
                print("XY9 - 4 from WinLoss Table           i1      :", XY9, file=f)
    
            XY10 = list(str(sum(int(XY8[0]), int(XY9[0])))) + list(str(sum(int(XY8[1]), int(XY9[1])))) + list(str(sum(int(XY8[2]), int(XY9[2])))) + list(str(sum(int(XY8[3]), int(XY9[3]))))
    
            print("Sum of Combined 1st and 2nd Plus WinLoss Table h1 and i1 is j1   :", XY10, file=f)
            a1188 = list(str(1)) + list(str(1)) + list(str(8)) + list(str(8))
    
            XY11 = list(str(sum(int(XY10[0]), int(a1188[0])))) + list(str(sum(int(XY10[1]), int(a1188[1])))) + list(str(sum(int(XY10[2]), int(a1188[2])))) + list(str(sum(int(XY10[3]), int(a1188[3]))))
    
            print("Sum after adding 1188        k1                  :", XY11, file=f)
    
            a8811 = list(str(8)) + list(str(8)) + list(str(1)) + list(str(1))
    
            XY12 = list(str(sum(int(XY10[0]), int(a8811[0])))) + list(str(sum(int(XY10[1]), int(a8811[1])))) + list(str(sum(int(XY10[2]), int(a8811[2])))) + list(str(sum(int(XY10[3]), int(a8811[3]))))
    
            print("Sum after adding 8811        l1                  :", XY12, file=f)
    
            print("Print k1 and l1                                  :", XY11, XY12, file=f)
    
            #XY13 = list(str(sum(int(XY11[0]), int(XY12[0])))) + list(str(sum(int(XY11[1]), int(XY12[1])))) + list(str(sum(int(XY11[2]), int(XY12[2])))) + list(str(sum(int(XY11[3]), int(XY12[3]))))
    
            #print("Sum from 1188 and 8811 results   k1 and l1 IGNORE    :", XY13, file=f)
    
            #XY14 = list(str(sum3(int(XY13[0]), int(XY13[0]), int(XY13[0])))) + list(str(sum3(int(XY13[1]), int(XY13[1]), int(XY13[1])))) + list(str(sum3(int(XY13[2]), int(XY13[2]), int(XY13[2])))) + list(str(sum3(int(XY13[3]), int(XY13[3]), int(XY13[3]))))
    
            #print("XY14                                             :", XY14, file=f)
    
            ThreePlusA =  sum(totalCountA, 3)
            ThreeMinusA = totalCountA - 3
            if ThreeMinusA <= 0:
                ThreeMinusA = 9 + ThreeMinusA
    
            ThreePlusB =  sum(totalCountB, 3)
            ThreeMinusB = totalCountB - 3
            if ThreeMinusB <= 0:
                ThreeMinusB = 9 + ThreeMinusB
    
            XY15 = list(str(ThreePlusA)) + list(str(ThreeMinusA)) + list(str(ThreePlusB)) + list(str(ThreeMinusB))
    
            print("XY15                                 T1          :", XY15, file=f)
    
            GetA0 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(listA[0]))))
            GetA1 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(listA[1]))))
            GetA2 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(listA[2]))))
            GetA3 = list(str(totalCountA)) + list(str(getXvalue(totalCountA, int(listA[3]))))
    
            print("Get ListA with totalCountA                       :", GetA0, GetA1, GetA2, GetA3, file=f)
    
            GetB0 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(listB[0]))))
            GetB1 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(listB[1]))))
            GetB2 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(listB[2]))))
            GetB3 = list(str(totalCountB)) + list(str(getXvalue(totalCountB, int(listB[3]))))
    
            print("Get ListB with totalCountB                       :", GetB0, GetB1, GetB2, GetB3, file=f)
    
            GetAB = list(str(sum(int(GetA0[0]), int(GetB0[0])))) + list(str(sum(int(GetA0[1]), int(GetB0[1])))) + list(str(sum(int(GetA1[0]), int(GetB1[0])))) + list(str(sum(int(GetA1[1]), int(GetB1[1])))) + list(str(sum(int(GetA2[0]), int(GetB2[0])))) + list(str(sum(int(GetA2[1]), int(GetB2[1])))) + list(str(sum(int(GetA3[0]), int(GetB3[0])))) + list(str(sum(int(GetA3[1]), int(GetB3[1]))))
    
            print("GetAB                                            :", GetAB, file=f)
    
            #GetABTotal =  list(str(sum(int(GetAB[4]), int(GetAB[5])))) + list(str(sum(int(GetAB[6]), int(GetAB[7])))) + list(str(sum(int(GetAB[0]), int(GetAB[1])))) + list(str(sum(int(GetAB[2]), int(GetAB[3]))))
    
            GetABTotal =  list(str(sum(int(GetAB[0]), int(GetAB[1])))) + list(str(sum(int(GetAB[2]), int(GetAB[3])))) + list(str(sum(int(GetAB[4]), int(GetAB[5])))) + list(str(sum(int(GetAB[6]), int(GetAB[7])))) 
    
            print("GetABTotal                               m1      :", GetABTotal, file=f)
            print("Print TV Value                           n1      :", GetTV, file=f)
            xx1 = getXvalue(int(GetTV[0]), int(GetABTotal[0]))
            xx2 = getXvalue(int(GetTV[1]), int(GetABTotal[1]))
            xx3 = getXvalue(int(GetTV[2]), int(GetABTotal[2]))
            xx4 = getXvalue(int(GetTV[3]), int(GetABTotal[3]))
    
            XY16 = list(str(xx1)) + list(str(xx2)) + list(str(xx3)) + list(str(xx4))
    
            print("XY16                                 o1          :", XY16, file=f)
    
            N11 = list(str(totalCountA)) + list(str(9))
            N12 = list(str(totalCountB)) + list(str(9))
            N13 = list(str(sum(totalCountA,totalCountB))) + list(str(9))
    
            TotalO1 = list(str(sum(xx1, xx2))) + list(str(sum(xx3, xx4)))
    
            print("Total o1                                         :", TotalO1, file=f)
    
            N11P1 = N11 + TotalO1
            N12Q1 = N12 + TotalO1
            N13R1 = N13 + TotalO1
    
            print("P1                                               :",N11P1, file=f)
            print("Q1                                               :",N12Q1, file=f)
            print("R1                                               :",N13R1, file=f)
    
            XY17List = list(str(sum(int(N11P1[0]), int(XY9[0])))) + list(str(sum(int(N11P1[1]), int(XY9[1])))) + list(str(sum(int(N11P1[2]), int(XY9[2])))) + list(str(sum(int(N11P1[3]), int(XY9[3]))))
    
            print("X17                                  s1          :", XY17List, file=f)
    
            X18List = list(str(sum(int(XY17List[0]), int(XY15[0])))) + list(str(sum(int(XY17List[1]), int(XY15[1])))) + list(str(sum(int(XY17List[2]), int(XY15[2])))) + list(str(sum(int(XY17List[3]), int(XY15[3]))))
    
            print("X18List                              U1          :", X18List, file=f)
    
            XY15List = list(str(sum3(int(X18List[0]), int(XY11[0]), int(XY12[0])))) + list(str(sum3(int(X18List[1]), int(XY11[1]), int(XY12[1])))) + list(str(sum3(int(X18List[2]), int(XY11[2]), int(XY12[2])))) + list(str(sum3(int(X18List[3]), int(XY11[3]), int(XY12[3]))))
    
            print("XY15List                              V1          :", XY15List, file=f)
    
            X19List = list(str(sum(int(X18List[0]), int(XY15List[0])))) + list(str(sum(int(X18List[1]), int(XY15List[1])))) + list(str(sum(int(X18List[2]), int(XY15List[2])))) + list(str(sum(int(X18List[3]), int(XY15List[3]))))
    
            print("X19List                              X1          :", X19List, file=f)
    
    
            XY17List1 = list(str(sum(int(N12Q1[0]), int(XY9[0])))) + list(str(sum(int(N12Q1[1]), int(XY9[1])))) + list(str(sum(int(N12Q1[2]), int(XY9[2])))) + list(str(sum(int(N12Q1[3]), int(XY9[3]))))
    
            print("X17List1                                  s2          :", XY17List1, file=f)
    
            X18List1 = list(str(sum(int(XY17List1[0]), int(XY15[0])))) + list(str(sum(int(XY17List1[1]), int(XY15[1])))) + list(str(sum(int(XY17List1[2]), int(XY15[2])))) + list(str(sum(int(XY17List1[3]), int(XY15[3]))))
    
            print("X18List1                              U2          :", X18List1, file=f)
    
            XY15List1 = list(str(sum3(int(X18List1[0]), int(XY11[0]), int(XY12[0])))) + list(str(sum3(int(X18List1[1]), int(XY11[1]), int(XY12[1])))) + list(str(sum3(int(X18List1[2]), int(XY11[2]), int(XY12[2])))) + list(str(sum3(int(X18List1[3]), int(XY11[3]), int(XY12[3]))))
    
            print("XY15List1                              V2          :", XY15List1, file=f)
    
            X19List1 = list(str(sum(int(X18List1[0]), int(XY15List1[0])))) + list(str(sum(int(X18List1[1]), int(XY15List1[1])))) + list(str(sum(int(X18List1[2]), int(XY15List1[2])))) + list(str(sum(int(X18List1[3]), int(XY15List1[3]))))
    
            print("X19List1                              X2          :", X19List1, file=f)
    
            XY17List2 = list(str(sum(int(N13R1[0]), int(XY9[0])))) + list(str(sum(int(N13R1[1]), int(XY9[1])))) + list(str(sum(int(N13R1[2]), int(XY9[2])))) + list(str(sum(int(N13R1[3]), int(XY9[3]))))
    
            print("X17List2                                  s3          :", XY17List2, file=f)
    
            X18List2 = list(str(sum(int(XY17List2[0]), int(XY15[0])))) + list(str(sum(int(XY17List2[1]), int(XY15[1])))) + list(str(sum(int(XY17List2[2]), int(XY15[2])))) + list(str(sum(int(XY17List2[3]), int(XY15[3]))))
    
            print("X18List2                              U3          :", X18List2, file=f)
    
            XY15List2 = list(str(sum3(int(X18List2[0]), int(XY11[0]), int(XY12[0])))) + list(str(sum3(int(X18List2[1]), int(XY11[1]), int(XY12[1])))) + list(str(sum3(int(X18List2[2]), int(XY11[2]), int(XY12[2])))) + list(str(sum3(int(X18List2[3]), int(XY11[3]), int(XY12[3]))))
    
            print("XY15List2                              V3          :", XY15List2, file=f)
    
            X19List2 = list(str(sum(int(X18List2[0]), int(XY15List2[0])))) + list(str(sum(int(X18List2[1]), int(XY15List2[1])))) + list(str(sum(int(X18List2[2]), int(XY15List2[2])))) + list(str(sum(int(X18List2[3]), int(XY15List2[3]))))
    
            print("X19List2                              X3          :", X19List2, file=f)
    
            P10X1 = list(str(sum(int(X19List[0]), int(X19List[1])))) + list(str(sum(int(X19List[2]), int(X19List[3]))))
            P10X1 = list(str(sum(int(P10X1[0]), int(P10X1[1]))))
            P10X2 = list(str(sum(int(X19List1[0]), int(X19List1[1])))) + list(str(sum(int(X19List1[2]), int(X19List1[3]))))
            P10X2 = list(str(sum(int(P10X2[0]), int(P10X2[1]))))
            P10X3 = list(str(sum(int(X19List2[0]), int(X19List2[1])))) + list(str(sum(int(X19List2[2]), int(X19List2[3]))))
            P10X3 = list(str(sum(int(P10X3[0]), int(P10X3[1]))))
    
            print("X1  X2  X3                                       :", P10X1, P10X2, P10X3, file=f)
            p = sum(int(DisplayMatrix3[1]), int(DisplayMatrix3[3]))
            q = sum(int(DisplayMatrix1[1]), int(DisplayMatrix1[3]))
            r = sum(int(DisplayMatrix2[1]), int(DisplayMatrix2[3]))
    
            x1p = list(str(P10X1[0]) + str(p))
            x1q = list(str(P10X1[0]) + str(q))
            x1r = list(str(P10X1[0]) + str(r))
    
            x2p = list(str(P10X2[0]) + str(p))
            x2q = list(str(P10X2[0]) + str(q))
            x2r = list(str(P10X2[0]) + str(r))
    
            x3p = list(str(P10X3[0]) + str(p))
            x3q = list(str(P10X3[0]) + str(q))
            x3r = list(str(P10X3[0]) + str(r))
    
            x123pqr  = list(str(sum3(int(x1p[0]), int(x2p[0]), int(x3p[0])))) + list(str(sum3(int(x1p[1]), int(x2p[1]), int(x3p[1])))) + list(str(sum3(int(x1q[0]), int(x2q[0]), int(x3q[0])))) + list(str(sum3(int(x1q[1]), int(x2q[1]), int(x3q[1])))) + list(str(sum3(int(x1r[0]), int(x2r[0]), int(x3r[0])))) + list(str(sum3(int(x1r[1]), int(x2r[1]), int(x3r[1]))))
    
            print("x123 PQR sum3 Before calculating A                   :", x123pqr, file=f)
    
            x123pqrA = list(x123pqr[0]) + list(x123pqr[1]) + list(str(sum(int(x123pqr[2]), int(x123pqr[3])))) + list(str(sum(int(x123pqr[4]), int(x123pqr[5]))))
    
    
            x1p = getXvalue(int(P10X1[0]), int(p))
            x1p = list(str(P10X1[0]) + str(x1p))
    
            x1q = getXvalue(int(P10X1[0]), int(q))
            x1q = list(str(P10X1[0]) + str(x1q))
    
            x1r = getXvalue(int(P10X1[0]), int(r))
            x1r = list(str(P10X1[0]) + str(x1r))
    
            x2p = getXvalue(int(P10X2[0]), int(p))
            x2p = list(str(P10X2[0]) + str(x2p))
    
            x2q = getXvalue(int(P10X2[0]), int(q))
            x2q = list(str(P10X2[0]) + str(x2q))
    
            x2r = getXvalue(int(P10X2[0]), int(r))
            x2r = list(str(P10X2[0]) + str(x2r))
    
            x3p = getXvalue(int(P10X3[0]), int(p))
            x3p = list(str(P10X3[0]) + str(x3p))
    
            x3q = getXvalue(int(P10X3[0]), int(q))
            x3q = list(str(P10X3[0]) + str(x3q))
    
            x3r = getXvalue(int(P10X3[0]), int(r))
            x3r = list(str(P10X3[0]) + str(x3r))
    
            x123pqr  = list(str(sum3(int(x1p[0]), int(x2p[0]), int(x3p[0])))) + list(str(sum3(int(x1p[1]), int(x2p[1]), int(x3p[1])))) + list(str(sum3(int(x1q[0]), int(x2q[0]), int(x3q[0])))) + list(str(sum3(int(x1q[1]), int(x2q[1]), int(x3q[1])))) + list(str(sum3(int(x1r[0]), int(x2r[0]), int(x3r[0])))) + list(str(sum3(int(x1r[1]), int(x2r[1]), int(x3r[1]))))
    
            print("x123 PQR sum3 Before Calculating B                       :", x123pqr, file=f)
    
            x123pqrB = list(x123pqr[0]) + list(x123pqr[1]) + list(str(sum(int(x123pqr[2]), int(x123pqr[3])))) + list(str(sum(int(x123pqr[4]), int(x123pqr[5]))))
    
            x1p = getXvalue(int(p), int(P10X1[0]))
            x1p = list(str(p) + str(x1p))
    
            x1q = getXvalue(int(q), int(P10X1[0]))
            x1q = list(str(q) + str(x1q))
    
            x1r = getXvalue(int(r), int(P10X1[0]))
            x1r = list(str(r) + str(x1r))
    
            x2p = getXvalue(int(p), int(P10X2[0]))
            x2p = list(str(p) + str(x2p))
    
            x2q = getXvalue(int(q), int(P10X2[0]))
            x2q = list(str(q) + str(x2q))
    
            x2r = getXvalue(int(r), int(P10X2[0]))
            x2r = list(str(r) + str(x2r))
    
            x3p = getXvalue(int(p), int(P10X3[0]))
            x3p = list(str(p) + str(x3p))
    
            x3q = getXvalue(int(q), int(P10X3[0]))
            x3q = list(str(q) + str(x3q))
    
            x3r = getXvalue(int(r), int(P10X3[0]))
            x3r = list(str(r) + str(x3r))
    
            x123pqr  = list(str(sum3(int(x1p[0]), int(x1q[0]), int(x1r[0])))) + list(str(sum3(int(x1p[1]), int(x1q[1]), int(x1r[1])))) + list(str(sum3(int(x2p[0]), int(x2q[0]), int(x2r[0])))) + list(str(sum3(int(x2p[1]), int(x2q[1]), int(x2r[1])))) + list(str(sum3(int(x3p[0]), int(x3q[0]), int(x3r[0])))) + list(str(sum3(int(x3p[1]), int(x3q[1]), int(x3r[1]))))
            print("x123 PQR sum3 Before Calculating C value                     :", x123pqr, file=f)
    
            x123pqrC = list(x123pqr[0]) + list(x123pqr[1]) + list(str(sum(int(x123pqr[2]), int(x123pqr[3])))) + list(str(sum(int(x123pqr[4]), int(x123pqr[5]))))
    
            print('A value                                                      :', x123pqrA, file=f)
            print('B value                                                      :', x123pqrB, file=f)
            print('C value                                                      :', x123pqrC, file=f)
    
            D  = list(str(sum3(int(x123pqrA[0]), int(x123pqrB[0]), int(x123pqrC[0])))) + list(str(sum3(int(x123pqrA[1]), int(x123pqrB[1]), int(x123pqrC[1])))) + list(str(sum3(int(x123pqrA[2]), int(x123pqrB[2]), int(x123pqrC[2])))) + list(str(sum3(int(x123pqrA[3]), int(x123pqrB[3]), int(x123pqrC[3]))))
    
            print('D value                                                      :', D, file=f)
            
            # Sum of Part1to6 + part8Result + Part9Result
            Part1to689 = list(str(sum3(int(Part1to6[0]), int(part8Result[0]), int(Part9Result[0])))) + list(str(sum3(int(Part1to6[1]), int(part8Result[1]), int(Part9Result[1])))) + list(str(sum3(int(Part1to6[2]), int(part8Result[2]), int(Part9Result[2])))) + list(str(sum3(int(Part1to6[3]), int(part8Result[3]), int(Part9Result[3]))))
            E = Part1to689
            print("Sum of Part1to6 + part8Result + Part9Result                  :", Part1to689, file=f)
            # Sum of BattleFieldValue + WinMaxValue + part5SS
            #import pdb;pdb.set_trace()
            BattleWinmaxSS  = list(
                                    str(sum3(int(BattleFieldValue[0]), int(WinMaxValue[0]), int(part5SS[0])))
                                ) + list(
                                    str(sum3(int(BattleFieldValue[1]), int(WinMaxValue[1]), int(part5SS[1])))
                                ) + list(
                                    str(sum3(int(BattleFieldValue[2]), int(WinMaxValue[2]), int(part5SS[2])))
                                ) + list(
                                    str(sum3(int(BattleFieldValue[3]), int(WinMaxValue[3]), int(part5SS[3])))
                                )
            F = BattleWinmaxSS
            print("Sum of BattleFieldValue + WinMaxValue + part5SS              :", BattleWinmaxSS, file=f)
            # Sum of E + F 
            AllMax = list(str(sum(int(E[0]), int(F[0])))) + list(str(sum(int(E[1]), int(F[1])))) + list(str(sum(int(E[2]), int(F[2])))) + list(str(sum(int(E[3]), int(F[3]))))
            print('All Max value                                                :', AllMax, file=f)
            
            K = list(str(sum(int(D[0]), int(part5SS[0])))) + list(str(sum(int(D[1]), int(part5SS[1])))) + list(str(sum(int(D[2]), int(part5SS[2])))) + list(str(sum(int(D[3]), int(part5SS[3]))))
            print('K value                                                      :', K, file=f)
            print("X1  X2  X3                                                   :", P10X1, P10X2, P10X3, file=f)
            #F has sum of Battle + Winmax + SS 
            TickValue  = list(
                                    str(sum4(int(F[0]), int(AllMax[0]), int(K[0]), int(setValues[0])))
                                ) + list(
                                    str(sum4(int(F[1]), int(AllMax[1]), int(K[1]), int(setValues[1])))
                                ) + list(
                                    str(sum4(int(F[2]), int(AllMax[2]), int(K[2]), int(setValues[2])))
                                ) + list(
                                    str(sum4(int(F[3]), int(AllMax[3]), int(K[3]), int(setValues[3])))
                                ) 
            print("TickValue                                                    :", TickValue, file=f)
            print("Display Matrix 1 Person A                                    :", list(str(DM1a)) + list(str(DM1b)) +  list(str(DM1c)) + list(str(DM1d)), file=f)
            print("Display Matrix 1 Person A - M Value                          :", DM1M, file=f)
            print("Display Matrix 2 Person B                                    :", list(str(DM2a)) + list(str(DM2b)) +  list(str(DM2c)) + list(str(DM2d)), file=f)
            print("Display Matrix 2 Person B - N Value                          :", DM2N, file=f)
            print("Display Matrix 3 Person C                                    :", list(str(DM3a)) + list(str(DM3b)) +  list(str(DM3c)) + list(str(DM3d)), file=f)
            print("Display Matrix 3 Person C - L Value                          :", DM3L, file=f)
            print("M and L Values                                               :", DM1M + DM3L, file=f)
            print("N and L Values                                               :", DM2N + DM3L, file=f)
            print("ML and NL Values ares                                                                    :", ML, NL, file=f)
            
            listAB = list(str(sum(int(listA[0]), int(listB[0])))) + list(str(sum(int(listA[1]), int(listB[1])))) + list(str(sum(int(listA[2]), int(listB[2])))) + list(str(sum(int(listA[3]), int(listB[3]))))
            print ("List of A                                                   :", listA, file=f)
            print ("List of B                                                   :", listB, file=f)
            print("Sum of List A and B                                          :", listAB, file=f)
            
            listML = DM1M + DM3L
            listNL = DM2N + DM3L
    
            listMLNL = list(str(sum(int(listML[0]), int(listNL[0])))) + list(str(sum(int(listML[1]), int(listNL[1])))) + list(str(sum(int(listML[2]), int(listNL[2])))) + list(str(sum(int(listML[3]), int(listNL[3]))))
    
            print("Sum of List ML and NL                                        :", listMLNL, file=f)
    
            ListABMLNL = list(str(sum(int(listAB[0]), int(listMLNL[0])))) + list(str(sum(int(listAB[1]), int(listMLNL[1])))) + list(str(sum(int(listAB[2]), int(listMLNL[2])))) + list(str(sum(int(listAB[3]), int(listMLNL[3]))))
    
            print("Sum of List AB and MLNL                                      :", ListABMLNL, file=f)
            
            ListTickABMLNL = list(str(sum(int(TickValue[0]), int(ListABMLNL[0])))) + list(str(sum(int(TickValue[1]), int(ListABMLNL[1])))) + list(str(sum(int(TickValue[2]), int(ListABMLNL[2])))) + list(str(sum(int(TickValue[3]), int(ListABMLNL[3]))))
    
            print("Sum of TickValue and ABMLNL                                  :", ListTickABMLNL, file=f)
    
            XTickValueABMLNL = list(str(sum(int(ListTickABMLNL[0]), int(ListTickABMLNL[1])))) + list(str(sum(int(ListTickABMLNL[2]), int(ListTickABMLNL[3]))))
            print("Final X value from TickValue and ABMLNL                      :", XTickValueABMLNL, file=f)
            print("X1  X2  X3                                                   :", P10X1, P10X2, P10X3, file=f)
    
            print("===== V11 Version Calculation Begins ========================", file=f)
    
            print("====== V11 Values after arranging with Matrix C for both A and B=========", file=f)
    
            v11CA1 = list(str(a2res[0])) + list(str(a2res[1])) + list(str(ares[0])) + list(str(TotalA[0]))
            v11CA2 = list(str(a2res[0])) + list(str(a2res[1])) + list(str(ares[1])) + list(str(TotalA[1]))
            v11CA3 = list(str(TotalC[0])) + list(str(TotalC[1])) + list(str(ares[0])) + list(str(TotalA[0]))
            v11CA4 = list(str(TotalC[0])) + list(str(TotalC[1])) + list(str(ares[1])) + list(str(TotalA[1]))
    
            v11CB1 = list(str(a2res[0])) + list(str(a2res[1])) + list(str(a1res[0])) + list(str(TotalB[0]))
            v11CB2 = list(str(a2res[0])) + list(str(a2res[1])) + list(str(a1res[1])) + list(str(TotalB[1]))
            v11CB3 = list(str(TotalC[0])) + list(str(TotalC[1])) + list(str(a1res[0])) + list(str(TotalB[0]))
            v11CB4 = list(str(TotalC[0])) + list(str(TotalC[1])) + list(str(a1res[1])) + list(str(TotalB[1]))
    
    
            print(v11CA1, file=f)
            print(v11CA2, file=f)
            print(v11CA3, file=f)
            print(v11CA4, file=f)      
            print(v11CB1, file=f)
            print(v11CB2, file=f)      
            print(v11CB3, file=f)
            print(v11CB4, file=f)
    
            print("====== V11 Values after arranging with Matrix C for both A and B=========", file=f)
            
            v11A1A2list = list(str(sum(int(v11CA1[0]) , int(v11CA2[0])))) + list(str(sum(int(v11CA1[1]) , int(v11CA2[1])))) + list(str(sum(int(v11CA1[2]) , int(v11CA2[2])))) + list(str(sum(int(v11CA1[3]) , int(v11CA2[3]))))
            v11A1A2total= sum4(int(v11A1A2list[0]) , int(v11A1A2list[1]), int(v11A1A2list[2]), int(v11A1A2list[3]))
            print("v11A1A2 Total                                    :", v11A1A2total, file=f)
            
            v11A3A4list = list(str(sum(int(v11CA3[0]) , int(v11CA4[0])))) + list(str(sum(int(v11CA3[1]) , int(v11CA4[1])))) + list(str(sum(int(v11CA3[2]) , int(v11CA4[2])))) + list(str(sum(int(v11CA3[3]) , int(v11CA4[3]))))
            v11A3A4total= sum4(int(v11A3A4list[0]) , int(v11A3A4list[1]), int(v11A3A4list[2]), int(v11A3A4list[3]))
            print("v11A3A4total Total                               :", v11A3A4total, file=f)
            
            v11B1B2list = list(str(sum(int(v11CB1[0]) , int(v11CB2[0])))) + list(str(sum(int(v11CB1[1]) , int(v11CB2[1])))) + list(str(sum(int(v11CB1[2]) , int(v11CB2[2])))) + list(str(sum(int(v11CB1[3]) , int(v11CB2[3]))))
            v11B1B2total= sum4(int(v11B1B2list[0]) , int(v11B1B2list[1]), int(v11B1B2list[2]), int(v11B1B2list[3]))
            print("v11B1B2list Total                                :", v11B1B2total, file=f)
            
            v11B3B4list = list(str(sum(int(v11CB3[0]) , int(v11CB4[0])))) + list(str(sum(int(v11CB3[1]) , int(v11CB3[1])))) + list(str(sum(int(v11CB3[2]) , int(v11CB4[2])))) + list(str(sum(int(v11CB3[3]) , int(v11CB4[3]))))
            v11B3B4total= sum4(int(v11B3B4list[0]) , int(v11B3B4list[1]), int(v11B3B4list[2]), int(v11B3B4list[3]))
            print("v11B3B4list Total                                :", v11B3B4total, file=f)
            
            v11K = list(str(v11A1A2total)) + list(str(v11A3A4total)) + list(str(v11B1B2total)) + list(str(v11B3B4total))
            
            v11OrthoList1 = list(str(get_ortho_values(v11A1A2total)))
            v11OrthoList2 = list(str(get_ortho_values(v11A3A4total)))
            v11OrthoList3 = list(str(get_ortho_values(v11B1B2total)))
            v11OrthoList4 = list(str(get_ortho_values(v11B3B4total)))
    
            
            print("v11OrthoList1", v11A1A2total, "=", v11OrthoList1, file=f)
            print("v11OrthoList1", v11A3A4total, "=", v11OrthoList2, file=f)
            print("v11OrthoList1", v11A3A4total, "=", v11OrthoList3, file=f)
            print("v11OrthoList1", v11B3B4total, "=", v11OrthoList4, file=f)
            
            v11OrthoTotal1 = sum4(int(v11OrthoList1[0]) , int(v11OrthoList2[0]), int(v11OrthoList3[0]), int(v11OrthoList4[0]))
            v11OrthoTotal2 = sum4(int(v11OrthoList1[1]) , int(v11OrthoList2[1]), int(v11OrthoList3[1]), int(v11OrthoList4[1]))
            v11OrthoTotal3 = sum4(int(v11OrthoList1[2]) , int(v11OrthoList2[2]), int(v11OrthoList3[2]), int(v11OrthoList4[2]))
            v11OrthoTotal4 = sum4(int(v11OrthoList1[3]) , int(v11OrthoList2[3]), int(v11OrthoList3[3]), int(v11OrthoList4[3]))
    
            v11L = list(str(v11OrthoTotal1)) + list(str(v11OrthoTotal2)) + list(str(v11OrthoTotal3)) + list(str(v11OrthoTotal4))
            
            v11M = list(str(sum(int(v11K[0]), int(v11L[0])))) + list(str(sum(int(v11K[1]), int(v11L[1])))) + list(str(sum(int(v11K[2]), int(v11L[2])))) + list(str(sum(int(v11K[3]), int(v11L[3]))))
    
            v11OrthoTickList1 = list(str(get_ortho_values(int(TickValue[0]))))
            v11OrthoTickList2 = list(str(get_ortho_values(int(TickValue[1]))))
            v11OrthoTickList3 = list(str(get_ortho_values(int(TickValue[2]))))
            v11OrthoTickList4 = list(str(get_ortho_values(int(TickValue[3]))))
            
            print("v11OrthoTickList1", TickValue[0], "=", v11OrthoTickList1, file=f)
            print("v11OrthoTickList2", TickValue[1], "=", v11OrthoTickList2, file=f)
            print("v11OrthoTickList3", TickValue[2], "=", v11OrthoTickList3, file=f)
            print("v11OrthoTickList4", TickValue[3], "=", v11OrthoTickList4, file=f)
    
            v11OrthoTickTotal1 = sum4(int(v11OrthoTickList1[0]) , int(v11OrthoTickList2[0]), int(v11OrthoTickList3[0]), int(v11OrthoTickList4[0]))
            v11OrthoTickTotal2 = sum4(int(v11OrthoTickList1[1]) , int(v11OrthoTickList2[1]), int(v11OrthoTickList3[1]), int(v11OrthoTickList4[1]))
            v11OrthoTickTotal3 = sum4(int(v11OrthoTickList1[2]) , int(v11OrthoTickList2[2]), int(v11OrthoTickList3[2]), int(v11OrthoTickList4[2]))
            v11OrthoTickTotal4 = sum4(int(v11OrthoTickList1[3]) , int(v11OrthoTickList2[3]), int(v11OrthoTickList3[3]), int(v11OrthoTickList4[3]))
    
            v11P = list(str(v11OrthoTickTotal1)) + list(str(v11OrthoTickTotal2)) + list(str(v11OrthoTickTotal3)) + list(str(v11OrthoTickTotal4))
    
    
            v11TurboTickList1 = list(str(get_turbo_values(int(TickValue[0]))))
            v11TurboTickList2 = list(str(get_turbo_values(int(TickValue[1]))))
            v11TurboTickList3 = list(str(get_turbo_values(int(TickValue[2]))))
            v11TurboTickList4 = list(str(get_turbo_values(int(TickValue[3]))))
            
            print("v11TurboTickList1", TickValue[0], "=", v11TurboTickList1, file=f)
            print("v11TurboTickList2", TickValue[1], "=", v11TurboTickList2, file=f)
            print("v11TurboTickList3", TickValue[2], "=", v11TurboTickList3, file=f)
            print("v11TurboTickList4", TickValue[3], "=", v11TurboTickList4, file=f)
    
            v11TurboTickTotal1 = sum4(int(v11TurboTickList1[0]) , int(v11TurboTickList2[0]), int(v11TurboTickList3[0]), int(v11TurboTickList4[0]))
            v11TurboTickTotal2 = sum4(int(v11TurboTickList1[1]) , int(v11TurboTickList2[1]), int(v11TurboTickList3[1]), int(v11TurboTickList4[1]))
            v11TurboTickTotal3 = sum4(int(v11TurboTickList1[2]) , int(v11TurboTickList2[2]), int(v11TurboTickList3[2]), int(v11TurboTickList4[2]))
            v11TurboTickTotal4 = sum4(int(v11TurboTickList1[3]) , int(v11TurboTickList2[3]), int(v11TurboTickList3[3]), int(v11TurboTickList4[3]))
    
            v11Q = list(str(v11TurboTickTotal1)) + list(str(v11TurboTickTotal2)) + list(str(v11TurboTickTotal3)) + list(str(v11TurboTickTotal4))
    
            v11R = list(str(sum(int(v11P[0]), int(v11Q[0])))) + list(str(sum(int(v11P[1]), int(v11Q[1])))) + list(str(sum(int(v11P[2]), int(v11Q[2])))) + list(str(sum(int(v11P[3]), int(v11Q[3]))))
    
            v11V = list(str(sum(int(v11M[0]), int(v11R[0])))) + list(str(sum(int(v11M[1]), int(v11R[1])))) + list(str(sum(int(v11M[2]), int(v11R[2])))) + list(str(sum(int(v11M[3]), int(v11R[3]))))
            
            v11totalAint = convert2int(TotalA) - 9
            print("TotalA Minus 9                               :",v11totalAint, file=f)
            v11totalAA = TotalA + list(str(v11totalAint))
            
            v11totalBint = convert2int(TotalB) - 9
            print("TotalB Minus 9                               :",v11totalBint, file=f)
            v11totalBB = TotalB + list(str(v11totalBint))
            
            v11totalCint = convert2int(TotalC) - 9
            print("TotalC Minus 9                               :",v11totalCint, file=f)
            v11totalCC = TotalC + list(str(v11totalCint))
            
            v11AC = list(str(sum(int(v11totalAA[0]), int(v11totalCC[0])))) + list(str(sum(int(v11totalAA[1]), int(v11totalCC[1])))) + list(str(sum(int(v11totalAA[2]), int(v11totalCC[2])))) + list(str(sum(int(v11totalAA[3]), int(v11totalCC[3]))))
            
            v11X = list(str(sum(int(v11AC[0]), int(v11AC[1])))) + list(str(sum(int(v11AC[2]), int(v11AC[3]))))
    
            v11BC = list(str(sum(int(v11totalBB[0]), int(v11totalCC[0])))) + list(str(sum(int(v11totalBB[1]), int(v11totalCC[1])))) + list(str(sum(int(v11totalBB[2]), int(v11totalCC[2])))) + list(str(sum(int(v11totalBB[3]), int(v11totalCC[3]))))
            
            v11Y = list(str(sum(int(v11BC[0]), int(v11BC[1])))) + list(str(sum(int(v11BC[2]), int(v11BC[3]))))
            
            v11XY = v11X + v11Y
    
            v11VandXX = list(str(sum(int(v11V[0]), int(v11XY[0])))) + list(str(sum(int(v11V[1]), int(v11XY[1])))) + list(str(sum(int(v11V[2]), int(v11XY[2])))) + list(str(sum(int(v11V[3]), int(v11XY[3]))))
    
            print("v11 K Value                              :", v11K, file=f)
            print("v11 L Value                              :", v11L, file=f)
            print("v11 M Value (K+L)                        :", v11M, file=f)
            print("v11 P Value                              :", v11P, file=f)
            print("v11 Q Value                              :", v11Q, file=f)
            print("v11 R Value (P+Q)                        :", v11R, file=f)
            print("v11 V Value (M+R)                        :", v11V, file=f)
            print("v11 AA Value                             :", v11totalAA, file=f)
            print("v11 BB Value                             :", v11totalBB, file=f)
            print("v11 CC Value                             :", v11totalCC, file=f)
            print("v11 AC Value                             :", v11AC, file=f)
            print("v11 BC Value                             :", v11BC, file=f)
            print("v11 X Value                              :", v11X, file=f)
            print("v11 Y Value                              :", v11Y, file=f)
            print("v11 XY Value                             :", v11XY, file=f)
            print("v11 V+XY Value                           :", v11VandXX, file=f)
    
    
            print("================= V11 Calculation END ===================", file=f)
            
    
            print(f'Execution logs saved at : {file_name}')
    
    except Exception as e:
        print(f'Exception occurred while execution : {str(e)}')
    
    

# ------------------ BABA PYTHON CORE ------------------ #
def run_baba_python():
    print("\n" + "="*90)
    print("🐍 BABA PYTHON v1.0 — FULL NEWSANJEEVI MERGED")
    print("="*90)

    print("\n[INFO] Running NEWSANJEEVI engine first...")
    run_newsanjeevi_full()

    print("\n[INFO] NEWSANJEEVI execution completed.")
    print("BABA PYTHON master engine ready for further extensions.")

if __name__ == "__main__":
    run_baba_python()
