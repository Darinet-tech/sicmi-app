"""Genera PDF y Excel a partir de una descripción neutral del documento."""
from dataclasses import dataclass, field
from decimal import Decimal
from io import BytesIO
from math import ceil
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AZUL = '#031999'
GRIS = '#e3e6ec'
CODIGO = 'CODIGO: PE-SG-020/18'
REVISION = 'REVISIÓN: 03'
EMITIDO = 'EMITIDO EL: 30/05/2021'
PROCEDIMIENTO = ('Procedimiento para el', 'Mantenimiento a Inmuebles con', 'Medios Propios')


@dataclass
class Documento:
    titulo: str
    registro: str
    archivo: str
    horizontal: bool = False
    bloques: list = field(default_factory=list)

    def campos(self, filas, cols=2):
        self.bloques.append(('campos', filas, cols))
        return self

    def tabla(self, titulo, cabeceras, filas, formatos=None, pesos=None, pie=None, min_filas=0, resaltar=None):
        """formatos: 'texto', 'cant' o 'dinero' por columna. pie: (etiqueta, valor) de la fila de total.
        resaltar: índices de filas (empezando en 0) que se muestran en negrita y con fondo gris."""
        n = len(cabeceras)
        self.bloques.append(('tabla', titulo, cabeceras, filas, formatos or ['texto'] * n,
                             pesos or [1] * n, pie, min_filas, set(resaltar or ())))
        return self

    def texto(self, etiqueta, texto, alto=12):
        self.bloques.append(('texto', etiqueta, texto or '', alto))
        return self

    def marcas(self, etiqueta, opciones):
        self.bloques.append(('marcas', etiqueta, opciones))
        return self

    def firmas(self, firmas):
        """firmas: lista de (cargo, nombre, fecha)."""
        self.bloques.append(('firmas', firmas))
        return self

    def parrafo(self, texto):
        self.bloques.append(('parrafo', texto))
        return self

    def imagen(self, ruta, alto_mm=95):
        self.bloques.append(('imagen', ruta, alto_mm))
        return self


def _num(v):
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def formatear(valor, formato):
    """Texto para el PDF: coma decimal y espacio de millares."""
    if valor is None:
        return ''
    if formato in ('dinero', 'cant') and _num(valor):
        d = Decimal(str(valor))
        s = f'{d:,.2f}' if formato == 'dinero' else f'{d:,.3f}'.rstrip('0').rstrip('.')
        return s.translate(str.maketrans({',': ' ', '.': ','}))
    return str(valor)


# ===================== PDF =====================
def _estilos():
    base = ParagraphStyle('base', fontName='Helvetica', fontSize=8.5, leading=11)
    return {
        'base': base,
        'etq': ParagraphStyle('etq', parent=base, fontName='Helvetica-Bold'),
        'etqder': ParagraphStyle('etqder', parent=base, fontName='Helvetica-Bold', alignment=2),
        'der': ParagraphStyle('der', parent=base, alignment=2),
        'cab': ParagraphStyle('cab', parent=base, fontName='Helvetica-Bold', textColor=colors.white, alignment=1),
        'titulo': ParagraphStyle('titulo', parent=base, fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=1),
        'reg': ParagraphStyle('reg', parent=base, fontSize=8, alignment=1, textColor=colors.HexColor('#5b6475')),
        'parr': ParagraphStyle('parr', parent=base, fontSize=9.5, leading=14, alignment=4),
    }


def _p(texto, estilo):
    return Paragraph(escape('' if texto is None else str(texto)).replace('\n', '<br/>'), estilo)


def _cabecera(canv, d):
    canv.saveState()
    w, h = canv._pagesize
    x0, x1 = 15 * mm, w - 15 * mm
    top, alto = h - 9 * mm, 20 * mm
    c1, c2 = x0 + 48 * mm, x1 - 58 * mm
    canv.setLineWidth(0.6)
    canv.rect(x0, top - alto, x1 - x0, alto)
    canv.line(c1, top, c1, top - alto)
    canv.line(c2, top, c2, top - alto)
    canv.setFillColor(colors.HexColor(AZUL))
    canv.setFont('Helvetica-Bold', 17)
    canv.drawString(x0 + 4 * mm, top - 10 * mm, 'ETECSA')
    canv.setFillColor(colors.black)
    canv.setFont('Helvetica', 7.5)
    canv.drawString(x0 + 4 * mm, top - 15 * mm, 'División de Logística y Servicios')
    canv.setFont('Helvetica', 9)
    medio = (c1 + c2) / 2
    for i, linea in enumerate(PROCEDIMIENTO):
        canv.drawCentredString(medio, top - (7 + i * 4.5) * mm, linea)
    canv.setFont('Helvetica-Bold', 8)
    canv.drawString(c2 + 3 * mm, top - 6 * mm, CODIGO)
    canv.setFont('Helvetica', 8)
    canv.drawString(c2 + 3 * mm, top - 10.5 * mm, REVISION)
    canv.drawString(c2 + 3 * mm, top - 15 * mm, EMITIDO)
    canv.drawRightString(x1 - 3 * mm, top - 18.5 * mm, f'Pág. {d.page}')
    canv.restoreState()


def _base_estilo():
    return [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]


def _pdf_campos(b, ancho, est):
    _, filas, cols = b
    celdas = []
    for i in range(0, len(filas), cols):
        fila = []
        for etq, val in filas[i:i + cols]:
            fila += [_p(etq, est['etq']), _p(val, est['base'])]
        fila += [''] * (cols * 2 - len(fila))
        celdas.append(fila)
    ancho_etq = {1: 55, 2: 38, 3: 28}.get(cols, 22) * mm
    t = Table(celdas, colWidths=[ancho_etq, (ancho - cols * ancho_etq) / cols] * cols)
    estilo = _base_estilo()
    for c in range(cols):
        estilo.append(('BACKGROUND', (c * 2, 0), (c * 2, -1), colors.HexColor(GRIS)))
    t.setStyle(TableStyle(estilo))
    return t


def _pdf_tabla(b, ancho, est):
    _, titulo, cab, filas, formatos, pesos, pie, min_filas, resaltar = b
    n = len(cab)
    anchos = [ancho * p / sum(pesos) for p in pesos]
    datos = []
    if titulo:
        datos.append([_p(titulo, est['cab'])] + [''] * (n - 1))
    datos.append([_p(c, est['cab']) for c in cab])
    primera = len(datos)  # índice de la primera fila de datos
    for i, fila in enumerate(filas):
        negrita = i in resaltar
        celdas = []
        for v, fm in zip(fila, formatos):
            if negrita:
                estilo_celda = est['etq'] if fm == 'texto' else est['etqder']
            else:
                estilo_celda = est['base'] if fm == 'texto' else est['der']
            celdas.append(_p(formatear(v, fm), estilo_celda))
        datos.append(celdas)
    for _ in range(max(0, min_filas - len(filas))):
        datos.append([_p(' ', est['base'])] * n)
    estilo = _base_estilo()
    h = 0
    if titulo:
        estilo += [('SPAN', (0, 0), (-1, 0)), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AZUL))]
        h = 1
    estilo.append(('BACKGROUND', (0, h), (-1, h), colors.HexColor(AZUL)))
    for i in resaltar:
        if i < len(filas):
            estilo.append(('BACKGROUND', (0, primera + i), (-1, primera + i), colors.HexColor(GRIS)))
    if pie:
        etiqueta, valor = pie
        datos.append([_p(etiqueta, est['etqder'])] + [''] * (n - 2) + [_p(formatear(valor, formatos[-1]), est['etqder'])])
        estilo += [('SPAN', (0, -1), (n - 2, -1)), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(GRIS))]
    t = Table(datos, colWidths=anchos, repeatRows=h + 1)
    t.setStyle(TableStyle(estilo))
    return t


def _pdf_texto(b, ancho, est):
    _, etq, texto, alto = b
    t = Table([[_p(etq, est['etq'])], [[_p(texto or ' ', est['base']), Spacer(1, alto * mm)]]], colWidths=[ancho])
    estilo = _base_estilo() + [('BACKGROUND', (0, 0), (0, 0), colors.HexColor(GRIS))]
    t.setStyle(TableStyle(estilo))
    return t


def _pdf_firmas(b, ancho, est):
    firmas = b[1]
    n = len(firmas)
    cabecera = [_p(cargo, est['cab']) for cargo, _, _ in firmas]
    cuerpo = [[_p(nom or ' ', est['base']),
               _p(f'Fecha: {fec}' if fec else 'Fecha: ____/____/______', est['base']),
               Spacer(1, 11 * mm),
               _p('Firma: ______________________', est['base'])] for _, nom, fec in firmas]
    t = Table([cabecera, cuerpo], colWidths=[ancho / n] * n)
    t.setStyle(TableStyle(_base_estilo() + [('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AZUL))]))
    return t


def _pdf_imagen(b, ancho):
    _, ruta, alto_mm = b
    with PILImage.open(ruta) as im:
        w, h = im.size
    esc = min(ancho / w, alto_mm * mm / h)
    t = Table([[RLImage(ruta, width=w * esc, height=h * esc)]], colWidths=[ancho])
    t.setStyle(TableStyle(_base_estilo() + [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    return t


def a_pdf(doc):
    est = _estilos()
    pagina = landscape(A4) if doc.horizontal else A4
    ancho = pagina[0] - 30 * mm
    buf = BytesIO()
    d = SimpleDocTemplate(buf, pagesize=pagina, leftMargin=15 * mm, rightMargin=15 * mm,
                          topMargin=34 * mm, bottomMargin=15 * mm, title=doc.titulo, author='SiCMI')
    hist = [_p(doc.titulo, est['titulo']), _p(doc.registro, est['reg']), Spacer(1, 4 * mm)]
    for b in doc.bloques:
        tipo = b[0]
        if tipo == 'campos':
            hist.append(_pdf_campos(b, ancho, est))
        elif tipo == 'tabla':
            hist.append(_pdf_tabla(b, ancho, est))
        elif tipo == 'texto':
            hist.append(_pdf_texto(b, ancho, est))
        elif tipo == 'firmas':
            hist.append(_pdf_firmas(b, ancho, est))
        elif tipo == 'imagen':
            hist.append(_pdf_imagen(b, ancho))
        elif tipo == 'parrafo':
            hist.append(_p(b[1], est['parr']))
        elif tipo == 'marcas':
            opciones = '      '.join(f'( {"X" if m else " "} ) {o}' for o, m in b[2])
            hist.append(Paragraph(f'<b>{escape(b[1])}:</b>&nbsp;&nbsp;{escape(opciones)}', est['base']))
        hist.append(Spacer(1, 3.5 * mm))
    d.build(hist, onFirstPage=_cabecera, onLaterPages=_cabecera)
    return buf.getvalue()


# ===================== EXCEL =====================
FINO = Side(style='thin', color='000000')
BORDE = Border(left=FINO, right=FINO, top=FINO, bottom=FINO)
R_AZUL = PatternFill('solid', fgColor='031999')
R_GRIS = PatternFill('solid', fgColor='E3E6EC')


def _lineas(texto, chars):
    return sum(max(1, ceil(len(t) / max(chars, 1))) for t in str(texto).split('\n'))


def _escribir(ws, fila, col, valor, hasta=None, negrita=False, relleno=None, color=None,
              alinear='left', formato=None, borde=True, tam=10):
    hasta = hasta or col
    if hasta > col:
        ws.merge_cells(start_row=fila, start_column=col, end_row=fila, end_column=hasta)
    for c in range(col, hasta + 1):
        if borde:
            ws.cell(fila, c).border = BORDE
        if relleno:
            ws.cell(fila, c).fill = relleno
    celda = ws.cell(fila, col, valor)
    celda.font = Font(bold=negrita, color=color, size=tam)
    celda.alignment = Alignment(wrap_text=True, vertical='top', horizontal=alinear)
    if formato:
        celda.number_format = formato
    return celda


def a_excel(doc):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Anexo'

    ncols = 2
    for b in doc.bloques:
        if b[0] == 'campos':
            ncols = max(ncols, b[2] * 2)
        elif b[0] == 'tabla':
            ncols = max(ncols, len(b[2]))
        elif b[0] == 'firmas':
            ncols = max(ncols, len(b[1]))
    base = max(13, min(34, 130 / ncols))
    anchos = [base] * ncols
    if ncols > 8:  # documentos muy anchos (Anexo 9): los pesos de la tabla reparten el ancho
        for b in doc.bloques:
            if b[0] == 'tabla' and len(b[2]) == ncols:
                total = 150 if doc.horizontal else 110
                s = sum(b[5])
                anchos = [max(4.5, total * p / s) for p in b[5]]
                break
    for c, w in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(c)].width = w

    def chars(a, b):  # caracteres que caben en las columnas a..b (1-based)
        return sum(anchos[a - 1:b]) * 1.05

    f = 1
    _escribir(ws, f, 1, 'ETECSA · División de Logística y Servicios', hasta=ncols,
              negrita=True, color='031999', borde=False, tam=12)
    f += 1
    _escribir(ws, f, 1, f'Procedimiento para el Mantenimiento a Inmuebles con Medios Propios · '
                        f'{CODIGO} · {REVISION} · {EMITIDO}', hasta=ncols, borde=False, color='5B6475', tam=8)
    f += 2
    _escribir(ws, f, 1, doc.titulo, hasta=ncols, negrita=True, alinear='center', borde=False, tam=13)
    ws.row_dimensions[f].height = 20 * _lineas(doc.titulo, chars(1, ncols) * 0.8)
    f += 1
    _escribir(ws, f, 1, doc.registro, hasta=ncols, alinear='center', borde=False, color='5B6475', tam=9)
    f += 2

    for b in doc.bloques:
        tipo = b[0]
        if tipo == 'campos':
            _, filas, cols = b
            seg = ncols // cols
            for i in range(0, len(filas), cols):
                altura = 15
                for j, (etq, val) in enumerate(filas[i:i + cols]):
                    ini = 1 + j * seg
                    fin = ncols if j == cols - 1 else ini + seg - 1
                    _escribir(ws, f, ini, etq, negrita=True, relleno=R_GRIS)
                    _escribir(ws, f, ini + 1, val or '', hasta=fin)
                    altura = max(altura, 15 * _lineas(etq, chars(ini, ini)),
                                 15 * _lineas(val or '', chars(ini + 1, fin)))
                ws.row_dimensions[f].height = altura
                f += 1

        elif tipo == 'tabla':
            _, titulo, cab, filas, formatos, pesos, pie, min_filas, resaltar = b
            n = len(cab)
            if titulo:
                _escribir(ws, f, 1, titulo, hasta=ncols, negrita=True, relleno=R_AZUL, color='FFFFFF', alinear='center')
                f += 1
            for c, h in enumerate(cab, start=1):
                _escribir(ws, f, c, h, hasta=ncols if c == n else None, negrita=True,
                          relleno=R_AZUL, color='FFFFFF', alinear='center')
            ws.row_dimensions[f].height = 18
            f += 1
            cuerpo = list(filas) + [[''] * n] * max(0, min_filas - len(filas))
            for i, fila in enumerate(cuerpo):
                resalta = i in resaltar
                altura = 15
                for c, (v, fm) in enumerate(zip(fila, formatos), start=1):
                    es_num = fm in ('dinero', 'cant') and _num(v)
                    valor = float(v) if es_num else ('' if v is None else v)
                    ultima = c == n
                    _escribir(ws, f, c, valor, hasta=ncols if ultima else None,
                              negrita=resalta, relleno=R_GRIS if resalta else None,
                              alinear='left' if fm == 'texto' else 'right',
                              formato=('#,##0.00' if fm == 'dinero' else 'General') if es_num else None)
                    if not es_num:
                        altura = max(altura, 15 * _lineas(valor, chars(c, ncols if ultima else c)))
                ws.row_dimensions[f].height = altura
                f += 1
            if pie:
                etiqueta, valor = pie
                _escribir(ws, f, 1, etiqueta, hasta=n - 1, negrita=True, relleno=R_GRIS, alinear='right')
                es_num = formatos[-1] in ('dinero', 'cant') and _num(valor)
                _escribir(ws, f, n, float(valor) if es_num else valor, hasta=ncols, negrita=True,
                          relleno=R_GRIS, alinear='right', formato='#,##0.00' if formatos[-1] == 'dinero' else None)
                f += 1

        elif tipo == 'texto':
            _, etq, texto, alto = b
            _escribir(ws, f, 1, etq, hasta=ncols, negrita=True, relleno=R_GRIS)
            f += 1
            _escribir(ws, f, 1, texto, hasta=ncols)
            ws.row_dimensions[f].height = max(alto * 3, 15 * _lineas(texto, chars(1, ncols)))
            f += 1

        elif tipo == 'marcas':
            opciones = '      '.join(f'( {"X" if m else " "} ) {o}' for o, m in b[2])
            _escribir(ws, f, 1, f'{b[1]}:   {opciones}', hasta=ncols, negrita=True)
            f += 1

        elif tipo == 'firmas':
            firmas = b[1]
            n = len(firmas)
            seg = ncols // n
            for j, (cargo, _, _) in enumerate(firmas):
                ini = 1 + j * seg
                _escribir(ws, f, ini, cargo, hasta=ncols if j == n - 1 else ini + seg - 1,
                          negrita=True, relleno=R_AZUL, color='FFFFFF', alinear='center')
            f += 1
            for j, (_, nom, fec) in enumerate(firmas):
                ini = 1 + j * seg
                _escribir(ws, f, ini, f'{nom or ""}\nFecha: {fec or "____/____/______"}\n\nFirma: ______________',
                          hasta=ncols if j == n - 1 else ini + seg - 1)
            ws.row_dimensions[f].height = 75
            f += 1

        elif tipo == 'imagen':
            _, ruta, alto_mm = b
            img = XLImage(ruta)
            w, h = img.width, img.height
            esc = min(sum(anchos) * 7 / w, alto_mm * 3.78 / h, 1)
            img.width, img.height = int(w * esc), int(h * esc)
            ws.add_image(img, f'A{f}')
            f += ceil(img.height / 20) + 1

        elif tipo == 'parrafo':
            _escribir(ws, f, 1, b[1], hasta=ncols, borde=False)
            ws.row_dimensions[f].height = 15 * _lineas(b[1], chars(1, ncols))
            f += 1
        f += 1

    ws.page_setup.orientation = 'landscape' if doc.horizontal else 'portrait'
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()