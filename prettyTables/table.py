'''
TABULADOR AUTOMATICO LIMITADO
'''

import time
import os

class table:
    
    def __init__(self, datos, estilo=0, alineacion=0, centVent=0):
        self.datos = datos
        self.estilo = estilo
        self.alineacion = alineacion
        self.centVent = centVent
        self.table = self.formatear(datos, estilo, alineacion, centVent)
        
    def ajustarDatos(self, datos, anchos, anchoVentana, altoVentana=""):

        datosDeLin = []
        datosOrd = []
        lineaAct = 0
        for linea in datos:
        
            datosOrd.append(linea)
            datoAct = 0
            lineasAgr = 0
        
            parSob = dict()
            iC = 0
            parSob["lineasPorAgr"] = 0

            for dato in linea:

                try:
                    parSob["partesExtra"]
                except:
                    parSob["partesExtra"] = {}

                if len(dato) > anchos[datoAct]:
                    
                    datosOrd[len(datosOrd)-1][datoAct] = datos[lineaAct][datoAct][0: anchos[datoAct]]
                    parSob["partesExtra"][iC] = {"indiceEnLi": datoAct, "partes": []}
                    inPart = anchos[datoAct]
                    fnPart = inPart + anchos[datoAct]
                    aumento = fnPart - inPart
                    partEx = len(dato) /  anchos[datoAct]

                    if partEx > float(round(partEx, 0)):
                        partExNt = int(round(partEx, 0)) + 1
                    else:
                        partExNt = int(round(partEx, 0))
                    partExNt -= 1

                    for x in range (0, partExNt):
                        parSob["partesExtra"][iC]["partes"].append(dato[inPart:fnPart])
                        inPart += aumento 
                        fnPart += aumento
                        if x + 1 > parSob["lineasPorAgr"]:
                            parSob["lineasPorAgr"] += 1

                    iC += 1
                datoAct += 1

            if len(parSob["partesExtra"]) > 0:

                lineasNuevas = []
                lineasAct = len(lineasNuevas)-1

                for nl in range(0, parSob["lineasPorAgr"]):
                    lineasNuevas.append([" " for i in range (0, len(datos[0]))])
                    lineasAgr += 1
                for indLinExt in range(0, parSob["lineasPorAgr"]):
                    lineasAct += 1
                    for indExtra in parSob["partesExtra"].keys():
                        try:
                            indiceEnLi = parSob["partesExtra"][indExtra]["indiceEnLi"]
                            existe = True if indLinExt <= len(parSob["partesExtra"][indExtra]["partes"])-1 else False
                            partPorAg = parSob["partesExtra"][indExtra]["partes"][indLinExt] if existe else " "
                            lineasNuevas[indLinExt][indiceEnLi] = partPorAg
                        except ValueError:
                            pass

                for i in range(0, len(lineasNuevas)):
                    for datLinNuev in range (0, len(lineasNuevas[i])):
                        for char in range(0, len(lineasNuevas[i][datLinNuev])):
                            if len(lineasNuevas[i][datLinNuev]) > 1:
                                if char == 0 and lineasNuevas[i][datLinNuev][char] == " ":
                                    sinEspa = lineasNuevas[i][datLinNuev].replace(" ", "")
                                    lineasNuevas[i][datLinNuev] = sinEspa

                    datosOrd.append(lineasNuevas[i])
                    datosDeLin.append(len(datosOrd)-1)
            lineaAct += 1
        
        return datosOrd, datosDeLin

    def anchoVentana(self):
        if os.name == "nt":
            mode = os.popen('mode').read().split()
            lineas = "L¡neas:" if "L¡neas:" in mode else ("Líneas" if "Líneas" in mode else "Lines")
            cols = "Columnas:" if "Columnas:" in mode else "Columns:"
            lineasInd = mode.index(lineas)+1
            colInd = mode.index(cols)+1
            lineas = mode[lineasInd]
            columnas = mode[colInd]
        else:
            lineas, columnas = os.popen('stty size', 'r').read().split()
        
        return lineas, columnas

    def maxLargoCol(self, datos, centVent=1):
        '''
        Aqui se comprueba si todas las filas tienen el mismo ancho
        '''
        # falta completar comprobación del mismo ancho

        anchoFilas = []
        for fila in datos:
            anchoFilas.append(len(fila))
        maxAnchoFilas = max(anchoFilas)


        '''Se obtiene el maximo valor de cada columna'''

        # lins = len(datos)
        cols = len(datos[0])
        vent = self.anchoVentana()
        # linsVent = int(vent[0])
        colsVent = int(vent[1])
        # altoUnaFila = round(linsVent / lins)
        anchoUnaCol = round(colsVent / cols)

        maxAnchoCoulumnas = []

        for columna in range (0, maxAnchoFilas):
            anchosUnaColumna = []
            for fila in datos:
                if centVent == 0:
                    anchosUnaColumna.append(len(str(fila[columna])))
                elif centVent == 1:
                    lenDato = len(str(fila[columna]))
                    anchoSiguiente = lenDato + (anchoUnaCol - lenDato)
                    anchosUnaColumna.append(anchoSiguiente)
            maxAnchoCoulumnas.append(max(anchosUnaColumna))

        """ Si la tabla es mas ancha que la ventana, se ajustan los anchos """

        anchoTabla = 2
        for ancho in maxAnchoCoulumnas:
            anchoTabla += ancho + 1
        
        anchoColMayor = max(maxAnchoCoulumnas)
        if centVent == 1:
            if anchoTabla > colsVent:

                for x in range (0, len(maxAnchoCoulumnas)):
                    maxAnchoCoulumnas[x] -= (round((anchoTabla-colsVent)/len(maxAnchoCoulumnas))) if maxAnchoCoulumnas[x] == anchoColMayor else 0
        else:
            if anchoTabla > colsVent:
                diferencia = anchoTabla - colsVent
                while diferencia > 0:
                    for i in range(0, len(maxAnchoCoulumnas)):
                        if maxAnchoCoulumnas[i] > 5:
                            maxAnchoCoulumnas[i] -= 1
                            diferencia -= 1

        return maxAnchoCoulumnas, colsVent

    def alinearDato(self, datoCelda, espacio, centroCelda, paso, anchoDatoCelda, anchoColumna):
        if espacio != centroCelda:
            # Aqui se añade el espacio después del dato
            if paso > 0 or (paso == 0 and anchoDatoCelda < anchoColumna):
                return " "
        else:
            return datoCelda

    def formatear(self, datos, estilo=0, alineacion=0, centVent=0):
        '''
        Los datos deben ingresarse en el siguiente formato:

            [[Encabezado_col1, Encabezado_col2],[Dato_col1, Dato_col2]...]

        Un arreglo de arreglos conforma la tabla.Cada sub-arreglo conforma las filas.
        Los datos con los mismo índices de cada arreglo conformanlas columnas.

        El primer arreglo es el encabezado, pero se trata igual que 
        los demas.

        ESTILOS
                                        
        NUM   ENCABEZADO   CUERPO
        
        0        ╝═║        ┘─│
        1
        2        =o         +-|
        3        ###        ...
                                        
        ALINEACIONES
            0: Izquierda
            1: Centrado
            2: Derecha
        
            
        centVent
            0: Tabla ajustada al tamaño de los valores
            1: Tabla ajustada a la ventana de la consola
        '''

        datos = [[f'{col}' for col in row] for row in datos]

        largos = self.maxLargoCol(datos, centVent)
        anchoColumnas = largos[0]

        ajuste = self.ajustarDatos(datos, largos[0], largos[1])
        datosAjustados = ajuste[0]
        datosDeLin = ajuste[1]

        """ ESTILOS """

        lineaHorizontal = ["─", " ", "-", ".", " ", " "]
        lineaHorizontalInferior = ["─", " ", "-", ".", "─", "═"]
        lineaVerticalIzquierda = ["│", " ", "│", ".", "│", "║"]
        lineaVerticalDerecha = ["│", " ", "│", ".", "│", "║"]
        lineaVertical = ["│", " ", "│", ".", "│", "│"]
        interseccion = ["┼", " ", "+", ".", " ", " "]
        interseccionDerecha = ["┤", " ", "+", ".", " ", " "]
        interseccionIzquierda = ["├", " ", "+", ".", " ", " "]
        interseccionSuperior = ["┬", " ", "+", ".", " ", " "]
        interseccionInferior = ["┴", " ", "+", ".", "┴", "═"]
        esquinaIzquierdaSuperior = ["┌", " ", "+", ".", " ", " "]
        esquinaIzquierdaInferior = ["└", " ", "+", ".", "└", "╚"]
        esquinaDerechaSuperior = ["┐", " ", "+", ".", " ", " "]
        esquinaDerechaInferior = ["┘", " ", "+", ".", "┘", "╝"]
        
        lineaHorizontalGruesa = ["═", " ", "=", "#", "─", "═"]
        lineaHorizontalGruesaInferior = ["═", " ", "=", "#", "─", "─"]
        lineaVerticalGruesaIzquierda = ["║", " ", " ", "#", "│", "║"]
        lineaVerticalGruesaDerecha = ["║", " ", " ", "#", "│", "║"]
        lineaVerticalGruesa = ["║", " ", " ", "#", " ", " "]
        interseccionGruesa = ["╬", " ", " ", "#", " ", " "]
        interseccionDerechaGruesa = ["╣", " ", "o", "#", " ", " "]
        interseccionIzquierdaGruesa = ["╠", " ", "o", "#", " ", " "]
        interseccionSuperiorGruesa = ["╦", " ", "o", "#", "─", "═"]
        interseccionInferiorGruesa = ["╩", " ", "o", "#", "┬", "┬"]
        esquinaIzquierdaSuperiorGruesa = ["╔", " ", "o", "#", "┌", "╔"]
        esquinaIzquierdaInferiorGruesa = ["╚", " ", "o", "#", "├", "║"]
        esquinaDerechaSuperiorGruesa = ["╗", " ", "o", "#", "┐", "╗"]
        esquinaDerechaInferiorGruesa = ["╝", " ", "o", "#", "┤", "║"]

        tabla = ''
        separadorSuperior = ''
        separadorInferior = ''
        separadorMedio = ''
        separadorSuperiorGrueso = ''
        separadorMedioGrueso = ''
        separadorinferiorGrueso = ''

        '''Se crean las cadenas que contienen los separadores horizontales'''
        for lugar in range (0, len(anchoColumnas)):
            if lugar == 0:
                separadorSuperior += esquinaIzquierdaSuperior[estilo]
                separadorSuperiorGrueso += esquinaIzquierdaSuperiorGruesa[estilo]
                separadorMedio += interseccionIzquierda[estilo]
                separadorMedioGrueso += interseccionIzquierdaGruesa[estilo]
                separadorInferior += esquinaIzquierdaInferior[estilo]
                separadorinferiorGrueso += esquinaIzquierdaInferiorGruesa[estilo]
            else:
                separadorSuperior += interseccionSuperior[estilo]
                separadorSuperiorGrueso += interseccionSuperiorGruesa[estilo]
                separadorMedio += interseccion[estilo]
                separadorMedioGrueso += interseccionGruesa[estilo]
                separadorInferior += interseccionInferior[estilo]
                separadorinferiorGrueso += interseccionInferiorGruesa[estilo]

            for x in range (0, anchoColumnas[lugar]):
                separadorSuperior += lineaHorizontal[estilo]
                separadorSuperiorGrueso += lineaHorizontalGruesa[estilo]
                separadorMedio += lineaHorizontal[estilo]
                separadorMedioGrueso += lineaHorizontalGruesa[estilo]
                separadorInferior += lineaHorizontalInferior[estilo]
                separadorinferiorGrueso += lineaHorizontalGruesaInferior[estilo]
        
        separadorSuperior += esquinaDerechaSuperior[estilo]
        separadorSuperiorGrueso += esquinaDerechaSuperiorGruesa[estilo]
        separadorMedio += interseccionDerecha[estilo]
        separadorMedioGrueso += interseccionDerechaGruesa[estilo]
        separadorInferior += esquinaDerechaInferior[estilo]
        separadorinferiorGrueso += esquinaDerechaInferiorGruesa[estilo]

        '''Se definen las filas (lineas)'''
        # El ciclo principal recorre cada arreglo "fila"
        paso = 0
        encabezado = 0
        linsGrues = 0
        unaVez = 1
        for fila in datosAjustados:

            col = 0
            anchoGuardado = 0

            # Se añade un separador horizontal
            if paso == 0:
                tabla += f'{separadorSuperiorGrueso}\n'
            elif paso not in datosDeLin and encabezado == 0:
                tabla += f'{separadorinferiorGrueso}\n'
                encabezado += 1
            else:
                if estilo not in [1, 4, 5] and paso not in datosDeLin:
                    tabla += f'{separadorMedio}\n'

            linea = ''

            # Este ciclo recorre cada dato en las filas
            # dato = 0
            for datoCelda in fila:
                
                '''
                Aquí se establece el valor que centra el dato.
                El ancho del dato y de la columna se restan para obtener
                el espacio de margen al rededor del dato.
                '''
                anchoDatoCelda = len(str(datoCelda))
                anchoColumna = anchoColumnas[anchoGuardado]
                espacioSobrante = anchoColumnas[anchoGuardado] - anchoDatoCelda + 1
                
                '''
                Al dividir enteramente entre dos el espacio sobrante se obtiene la 
                posición en la que el ciclo siguiente pondrá el dato, para centrarlo
                '''
                centroCelda = round((espacioSobrante // 2))

                # Se añade un separador vertical en cada ciclo
                if paso not in datosDeLin and unaVez == 1:
                    linsGrues += 1
                
                if linsGrues > 0:
                    if col == 0:
                        linea += lineaVerticalGruesaIzquierda[estilo]
                    else:
                        linea += lineaVerticalGruesa[estilo]
                else:
                    if col == 0:
                        linea += lineaVerticalIzquierda[estilo]
                    else:
                        linea += lineaVertical[estilo]
                
                col += 1

                for espacio in range (0, espacioSobrante):

                    if alineacion == 0:
                        if fila == 0:
                            linea += self.alinearDato(datoCelda, espacio, centroCelda, paso, anchoDatoCelda, anchoColumna)
                        else:
                            linea += self.alinearDato(datoCelda, espacio, 0, paso, anchoDatoCelda, anchoColumna)
                    elif alineacion == 1:
                        linea += self.alinearDato(datoCelda, espacio, centroCelda, paso, anchoDatoCelda, anchoColumna)
                    elif alineacion == 2:
                        if fila == 0:
                            linea += self.alinearDato(datoCelda, espacio, centroCelda, paso, anchoDatoCelda, anchoColumna)
                        else:
                            derecha = anchoColumna-anchoDatoCelda
                            linea += self.alinearDato(datoCelda, espacio, centroCelda, paso, anchoDatoCelda, derecha)

                anchoGuardado += 1
            
            if linsGrues > 1:
                linea += lineaVerticalGruesaDerecha[estilo]
            else:
                linea += lineaVerticalDerecha[estilo]

            paso += 1
            if paso not in datosDeLin and linsGrues > 0:
                linsGrues = 0
                unaVez -= 1
            tabla += f'{linea}\n'

        tabla += f'{separadorInferior}\n'

        return tabla[:-1]
    
    
   
if __name__ == '__main__':



    import nltk
    from random import choice, randint

    style = input("Style (0 - 5): ")
    style = randint(0, 5) if style == "" else int(style)
    alignment = input("Alignment (0: left, 1: center): ")
    alignment = randint(0, 1) if alignment == "" else int(alignment)
    centerTable = input("Adjust table to window (0: no, 1: yes): ")
    centerTable = randint(0, 1) if centerTable == "" else int(centerTable)

    try:
        nltk.corpus.words.words()
    except:
        nltk.download("words")

    inicio = randint(2000, 200000)
    final = 10
    wordList = nltk.corpus.words.words()[inicio:inicio+final] + ["a", "x", "y", "b", "c", "v", "q", "w", "e", "o", "t", "g"]
    numeros = "1 3 2 4 5 6 7 8 9 0"
    letras = "a b c d e f g h i j k l m n ñ o p q r s t u v w x y z"

    encabezado = ["STRING","LEN","TYPE","ID"]
    datos = [encabezado]
    for x in range(0, len(wordList)):
        datos.append(['' for nuevo in encabezado])
        for y in range(0, len(encabezado)):
            if y == 0:
                datos[x+1][y] = wordList[x]
            elif y == 1:
                datos[x+1][y] = str(len(wordList[x]))
            elif y == 2:
                datos[x+1][y] = (choice(["Word", "String"])) if len(wordList[x]) > 1 else choice(["Letter", "Character"])
            else:
                tamaño = randint(30, 40)
                idEscogido = ""            

                for caracter in range(0, tamaño):
                    eleccion = randint(0, 1)
                    mayuscula = randint(0, 1)
                    aElegir = (numeros if eleccion==0 else letras).split()
                    caracter = choice(aElegir)
                    caracter.upper() if (caracter in letras and mayuscula == 1) else True
                    idEscogido += caracter

                datos[x+1][y] = idEscogido

    tabla = table(datos, style, alignment, centerTable).table
    print(tabla)

    input("Press enter to exit")