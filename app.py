from flask import Flask, request, send_file, render_template_string
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import tempfile
import os
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OLEOTRAX - Certificados</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e7a4d 0%, #2d9f65 100%);
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 20px;
            max-width: 500px;
            margin: 0 auto;
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .header h1 {
            color: #1e7a4d;
            font-size: 28px;
            margin-bottom: 5px;
        }
        .header p {
            color: #666;
            font-size: 13px;
            font-style: italic;
        }
        h2 {
            color: #1e7a4d;
            text-align: center;
            margin-bottom: 15px;
            font-size: 20px;
        }
        .info {
            background: #f0f9f4;
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #1e7a4d;
            margin-bottom: 20px;
            font-size: 13px;
            color: #555;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 6px;
            font-size: 14px;
        }
        input, textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #1e7a4d;
        }
        textarea {
            resize: vertical;
            min-height: 70px;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #1e7a4d 0%, #2d9f65 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
        }
        button:active {
            transform: scale(0.98);
        }
        @media (max-width: 500px) {
            .row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛢️ OLEOTRAX</h1>
            <p>"Juntos por um futuro mais limpo e sustentável."</p>
        </div>
        
        <h2>Gerador de Certificado</h2>
        
        <div class="info">
            <strong>✨ Certificado Profissional</strong><br>
            Preencha os dados da coleta.
        </div>
        
        <form method="POST" action="/gerar">
            <div class="form-group">
                <label>Data da Coleta *</label>
                <input type="date" name="data" required>
            </div>
            
            <div class="form-group">
                <label>Nome da Empresa *</label>
                <input type="text" name="empresa" required>
            </div>
            
            <div class="form-group">
                <label>CNPJ *</label>
                <input type="text" name="cnpj" required placeholder="12.345.678/0001-99">
            </div>
            
            <div class="form-group">
                <label>Endereço Completo *</label>
                <textarea name="endereco" required placeholder="Rua, número, bairro, cidade/estado"></textarea>
            </div>
            
            <div class="row">
                <div class="form-group">
                    <label>Quantidade (L) *</label>
                    <input type="number" name="quantidade" step="0.1" required>
                </div>
                <div class="form-group">
                    <label>Acondicionamento *</label>
                    <input type="text" name="acond" required placeholder="Ex: Bombona plástica 50L">
                </div>
            </div>
            
            <button type="submit">📄 Gerar Certificado PDF</button>
        </form>
    </div>
    
    <script>
        document.querySelector('input[type="date"]').valueAsDate = new Date();
    </script>
</body>
</html>
'''

def draw_wrapped_text(c, text, x, y, max_width, font_name='Helvetica', font_size=10):
    """Helper to draw text that wraps properly"""
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines:
        c.drawString(x, y, line)
        y -= font_size * 1.2  # Line spacing
    
    return y

def generate_pdf(data):
    """Generate the certificate PDF with proper text wrapping"""
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    c = canvas.Canvas(temp_pdf.name, pagesize=A4)
    w, h = A4
    
    # Parse date
    date_obj = datetime.strptime(data['data'], '%Y-%m-%d')
    dia = date_obj.day
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    mes = meses[date_obj.month - 1]
    ano = date_obj.year
    data_fmt = date_obj.strftime('%d/%m/%Y')
    
    # Green header
    c.setFillColor(HexColor('#1e7a4d'))
    c.rect(0, h - 50, w, 50, fill=1, stroke=0)
    
    # White circle
    c.setFillColor(HexColor('#ffffff'))
    c.circle(w/2, h - 25, 40, fill=1, stroke=0)
    
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, w/2 - 25, h - 49, width=50, height=50, mask='auto')
    
    # Title
    c.setFillColor(HexColor('#000000'))
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(w/2, h - 70, 'CERTIFICADO DE COLETA E DESCARTE')
    
    # Reset to black
    c.setFillColor(HexColor('#000000'))
    
    # Date
    y = h - 100
    c.setFont('Helvetica', 11)
    c.drawString(25, y, f'Data: {dia} de {mes} de {ano}')
    
    # Body text - use text wrapping
    y -= 20
    max_width = w - 50  # 25mm margins on each side
    
    # Paragraph 1
    para1 = f"Certificamos que {data['empresa']}, pessoa jurídica de direito privado, inscrita no CNPJ/MF sob nº {data['cnpj']}, com sede {data['endereco']}, destina seus resíduos de óleo e gordura vegetal de forma sustentável, dando um destino ambientalmente correto aos resíduos de gordura e óleo vegetal de seu estabelecimento."
    y = draw_wrapped_text(c, para1, 25, y, max_width, 'Helvetica', 10)
    
    # Paragraph 2
    y -= 8
    para2_part1 = "Os resíduos são armazenados de forma adequada, em recipientes específicos devidamente higienizados e fechados, sendo destinados pela"
    y = draw_wrapped_text(c, para2_part1, 25, y, max_width, 'Helvetica', 10)
    
    # Bold OLEOTRAX LTDA
    c.setFont('Helvetica-Bold', 10)
    c.drawString(25, y, 'OLEOTRAX LTDA')
    oleotrax_width = c.stringWidth('OLEOTRAX LTDA', 'Helvetica-Bold', 10)
    c.setFont('Helvetica', 10)
    c.drawString(25 + oleotrax_width + 5, y, ', CNPJ/MF nº')
    y -= 12
    
    c.setFont('Helvetica-Bold', 10)
    c.drawString(25, y, '59.750.105/0001-00, Autorização Ambiental IMA/SC nº 097/2025.')
    y -= 12
    
    # Paragraph 3
    c.setFont('Helvetica', 10)
    para3 = "Certificamos ainda, que o resíduo foi coletado e destinado de forma ambientalmente correta conforme segue:"
    y = draw_wrapped_text(c, para3, 25, y, max_width, 'Helvetica', 10)
    
    # Table
    y -= 15
    table_x = 25
    lw, vw, rh = 70, 110, 12
    
    rows = [
        ('Descrição', 'Óleo vegetal usado'),
        ('Quantidade', f"{data['quantidade']} L"),
        ('Unidade de Medida', 'Litros (L)'),
        ('Classe do Resíduo', 'Classe II'),
        ('Data de Recebimento', data_fmt),
        ('Acondicionamento', data['acond'][:25])
    ]
    
    c.setLineWidth(0.5)
    c.setStrokeColor(HexColor('#000000'))
    
    for label, value in rows:
        # Label cell (light green)
        c.setFillColor(HexColor('#dcf0dc'))
        c.rect(table_x, y - rh, lw, rh, fill=1, stroke=1)
        
        # Value cell (white)
        c.setFillColor(HexColor('#ffffff'))
        c.rect(table_x + lw, y - rh, vw, rh, fill=1, stroke=1)
        
        # Text - positioned INSIDE the cells properly
        c.setFillColor(HexColor('#000000'))
        c.setFont('Helvetica-Bold', 9)
        c.drawString(table_x + 3, y - 8, label)
        
        c.setFont('Helvetica', 9)
        c.drawString(table_x + lw + 3, y - 8, value)
        
        y -= rh
    
    # Footer
    c.setFillColor(HexColor('#787878'))
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, 45, 'OLEOTRAX LTDA')
    
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, 39, 'CNPJ: 59.750.105/0001-00 — Autorização Ambiental IMA/SC nº 097/2025')
    c.drawCentredString(w/2, 33, 'Telefone: (47) 99112-5906')
    
    c.setFont('Helvetica-Oblique', 9)
    c.drawCentredString(w/2, 25, '"Juntos por um futuro mais limpo e sustentável."')
    
    c.save()
    return temp_pdf.name

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/gerar', methods=['POST'])
def gerar():
    data = {
        'data': request.form['data'],
        'empresa': request.form['empresa'],
        'cnpj': request.form['cnpj'],
        'endereco': request.form['endereco'],
        'quantidade': request.form['quantidade'],
        'acond': request.form['acond']
    }
    
    pdf_path = generate_pdf(data)
    filename = f"Certificado_{data['empresa'].replace(' ', '_')}.pdf"
    
    return send_file(pdf_path, as_attachment=True, download_name=filename, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
