# prettyTables

This library is under development, and may suffer changes.

Feel free to make issues, suggestions, or pull requests.

## Instalation

### Windows

``pip install prettyTables``

### Ubuntu

``pip3 install prettyTables``

## Usage

```
from prettyTables import Table

headers = ['STRING', 'LEN', 'TYPE', 'ID']

data = [['gamelang Word', '13', 'Phrase', '1e8ñrz8ty136s66ñ4b8k38qn9ñadryzb5'],
        ['gameless Elongated', '18', 'Phrase', '4j4ycaicwenh2ñs25ñmmmr239ñ23w0bn803hcs'],
        ['gamelike', '8', 'Word', 'p2in3782mub17480eq72mq3pc7v9zon'],
        ['Gamelion', '8', 'String', '4hv2d710s6vsñ8n0ybfms2c301qr7dj'], 
        ['gamelotte', '9', 'Word', '1tg5y3jn7xf9046681qe8o1pul50c046w29xz'],
        ['gamely', '6', 'String', 'mq58xu8vq84x784ngcw44w5410u28fñ'],
        ['gamene', '6', 'Word', '98r75qj996c379tg1kñpz10dw534m22a'], 
        ['gameness', '8', 'String', 'yfv5886ff04sp7a1t8z30tugq3bx47jd'], 
        ['gamesome', '8', 'Word', 'owus19312vy2hube4rdha0ej9s98v28fz'], 
        ['gamesomely', '10', 'String', '0ms888ib3768p3khz32f8272456v219']]

style = 'bold_borderline'
alignment = 'left'
expandToWindow = False

newTable = Table(
  tabularData=data,
  headers=headers,
  strAlign=alignment,
  style=style,
  expandToWindow=expandToWindow
  )
newTable = newTable.make()

print(newTable)
  
```

##### Output

```
╔══════════════════════╤═══════╤══════════╤══════════════════════════════════════════╗
║ STRING               │ LEN   │ TYPE     │ ID                                       ║
╠══════════════════════╪═══════╪══════════╪══════════════════════════════════════════╣
║ gamelang Word        │ 13    │ Phrase   │ 1e8ñrz8ty136s66ñ4b8k38qn9ñadryzb5        ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gameless Elongated   │ 18    │ Phrase   │ 4j4ycaicwenh2ñs25ñmmmr239ñ23w0bn803hcs   ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gamelike             │ 8     │ Word     │ p2in3782mub17480eq72mq3pc7v9zon          ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ Gamelion             │ 8     │ String   │ 4hv2d710s6vsñ8n0ybfms2c301qr7dj          ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gamelotte            │ 9     │ Word     │ 1tg5y3jn7xf9046681qe8o1pul50c046w29xz    ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gamely               │ 6     │ String   │ mq58xu8vq84x784ngcw44w5410u28fñ          ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gamene               │ 6     │ Word     │ 98r75qj996c379tg1kñpz10dw534m22a         ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gameness             │ 8     │ String   │ yfv5886ff04sp7a1t8z30tugq3bx47jd         ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gamesome             │ 8     │ Word     │ owus19312vy2hube4rdha0ej9s98v28fz        ║
╟──────────────────────┼───────┼──────────┼──────────────────────────────────────────╢
║ gamesomely           │ 10    │ String   │ 0ms888ib3768p3khz32f8272456v219          ║
╚══════════════════════╧═══════╧══════════╧══════════════════════════════════════════╝
```

### Text Wrapping

It also wraps the text of the cells if the width of the window is less than the total width
of the table.

This is a dramatization using the previous example.

```
╔═════════════╤═════╤═════╤════════════════════════╗
║ STRING      │ LEN │ TYP │ ID                     ║  
║             │     │ E   │                        ║  
╠═════════════╪═════╪═════╪════════════════════════╣  
║ gamelang    │ 13  │ Wor │ 1e8ñrz8ty136s66ñ4b8k38 ║  
║ Word        │     │ d   │ qn9ñadryzb5            ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gameless    │ 18  │ Str │ 4j4ycaicwenh2ñs25ñmmmr ║  
║ Elongated   │     │ ing │ 239ñ23w0bn803hcs       ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gamelike    │ 8   │ Wor │ p2in3782mub17480eq72mq ║  
║             │     │ d   │ 3pc7v9zon              ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ Gamelion    │ 8   │ Str │ 4hv2d710s6vsñ8n0ybfms2 ║  
║             │     │ ing │ c301qr7dj              ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gamelotte   │ 9   │ Wor │ 1tg5y3jn7xf9046681qe8o ║  
║             │     │ d   │ 1pul50c046w29xz        ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gamely      │ 6   │ Str │ mq58xu8vq84x784ngcw44w ║  
║             │     │ ing │ 5410u28fñ              ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gamene      │ 6   │ Wor │ 98r75qj996c379tg1kñpz1 ║  
║             │     │ d   │ 0dw534m22a             ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gameness    │ 8   │ Str │ yfv5886ff04sp7a1t8z30t ║  
║             │     │ ing │ ugq3bx47jd             ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gamesome    │ 8   │ Wor │ owus19312vy2hube4rdha0 ║  
║             │     │ d   │ ej9s98v28fz            ║  
╟─────────────┼─────┼─────┼────────────────────────╢  
║ gamesomely  │ 10  │ Str │ 0ms888ib3768p3khz32f82 ║  
║             │     │ ing │ 72456v219              ║  
╚═════════════╧═════╧═════╧════════════════════════╝
```
