"""
IDENTIFIER COLUMNS

Integers that are identifiers -- folios, IDs, codes, SKUs, account or ticket
numbers, postal codes, years -- are read digit by digit and must not get
thousands separators: folio ``1281`` is not "one thousand two hundred
eighty-one", and ``1,281`` looks like a quantity. Money and quantity
columns keep their separators.

:func:`is_id_column` decides from the column name (configurable through
``names``), used by :class:`~flexablelib.Table` (``id_columns='auto'``) and
the interactive ``DataTable``.

>>> is_id_column('Folio'), is_id_column('No. cliente'), is_id_column('Total')
(True, True, False)
>>> is_id_column('No. de piezas')     # a quantity, despite the "No."
False
"""

import re
import unicodedata

__all__ = ['ID_COLUMN_NAMES', 'QUANTITY_WORDS', 'is_id_column',
           'normalize_header']

#: Words that make a column an identifier (accents and case ignored).
ID_COLUMN_NAMES = (
    'id', 'ids', 'folio', 'folios', 'codigo', 'code', 'clave', 'key', 'sku',
    'numero', 'num', 'no', 'nro', 'nº', 'n°', '#', 'number', 'ref',
    'referencia', 'reference', 'ticket', 'factura', 'invoice', 'pedido',
    'order', 'orden', 'serie', 'serial', 'lote', 'batch', 'ean', 'upc',
    'isbn', 'gtin', 'rfc', 'curp', 'nss', 'cp', 'zip', 'postal',
    'telefono', 'tel', 'phone', 'celular', 'extension', 'ext', 'matricula',
    'expediente', 'nomina', 'empleado', 'cuenta', 'account', 'tarjeta',
    'card', 'guia', 'tracking', 'año', 'ano', 'anio', 'year', 'ejercicio',
    'periodo', 'version', 'build', 'pin', 'nip', 'uuid', 'guid',
)

#: Words that make a column a quantity even with an identifier word in it
#: (``'No. de piezas'``, ``'Número de empleados'``).
QUANTITY_WORDS = (
    'piezas', 'pzas', 'unidades', 'articulos', 'items', 'productos',
    'cantidad', 'cantidades', 'qty', 'quantity', 'total', 'totales', 'monto',
    'importe', 'precio', 'price', 'amount', 'saldo', 'balance', 'horas',
    'hours', 'dias', 'days', 'veces', 'times', 'personas', 'people',
    'empleados', 'employees', 'clientes', 'customers', 'usuarios', 'users',
    'visitas', 'visits', 'ventas', 'sales', 'pedidos', 'orders', 'facturas',
    'invoices', 'tickets', 'registros', 'records', 'filas', 'rows',
    'existencias', 'stock', 'inventario', 'count', 'conteo', 'suma', 'sum',
    'costo', 'cost', 'kg', 'km', 'litros', 'metros', 'peso', 'weight',
)

_TOKEN = re.compile(r'[^\w#°º]+', re.UNICODE)


def normalize_header(header):
    """Lower case, without accents (``ñ`` kept), tokens split on symbols."""
    text = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', str(header).strip())
    text = text.lower().replace('ñ', '\0')
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return text.replace('\0', 'ñ')


def is_id_column(header, names=None, quantity_words=None):
    """
    Whether a column called ``header`` holds identifiers.

    True when the whole name, or one of its words, is in ``names``
    (default :data:`ID_COLUMN_NAMES`) and none of its words is in
    ``quantity_words`` (default :data:`QUANTITY_WORDS`); ``'cliente_id'``,
    ``'ID pedido'``, ``'Código postal'``, ``'Folio fiscal'`` and ``'Año'``
    are identifiers, ``'Total'`` and ``'No. de piezas'`` are not.
    """
    if header is None or isinstance(header, bool):
        return False
    names = ID_COLUMN_NAMES if names is None else names
    wanted = set(normalize_header(n) for n in names)
    quantity = set(normalize_header(q) for q in (
        QUANTITY_WORDS if quantity_words is None else quantity_words))
    text = normalize_header(header)
    if not text:
        return False
    if text in wanted or text.replace('.', '').replace(' ', '') in wanted:
        return True
    tokens = [t for t in _TOKEN.split(text.replace('_', ' ')) if t]
    if any(t in quantity for t in tokens):
        return False
    if text.startswith(('#', 'nº', 'n°')) and '#' in wanted:
        return True
    return any(t in wanted for t in tokens)
