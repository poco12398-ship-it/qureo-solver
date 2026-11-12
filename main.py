import os
import asyncio
from flask import Flask, render_template_string, request, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qureo Automation Tool</title>
    <style>
        body { font-family: system-ui, sans-serif; background-color: #0f172a; color: white; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border: 1px solid #334155; }
        h2 { text-align: center; color: #38bdf8; margin-top: 0; }
        label { display: block; margin-top: 15px; font-size: 14px; color: #94a3b8; }
        input { width: 100%; padding: 12px; margin-top: 5px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: white; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; margin-top: 20px; background: #0284c7; border: none; border-radius: 8px; color: white; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:disabled { background: #475569; cursor: not-allowed; }
        #log { margin-top: 20px; padding: 12px; background: #090d16; border-radius: 8px; font-family: monospace; font-size: 13px; color: #4ade80; min-height: 80px; max-height: 150px; overflow-y: auto; white-space: pre-wrap; border: 1px solid #1e293b; }
    </style>
</head>
<body>
    <div class="card">
        <h2>⚡ Qureo Solver</h2>
        <label>كود الطالب:</label>
        <input type="text" id="studentCode" value="472029231">
        
        <label>كلمة المرور:</label>
        <input type="password" id="password" value="Nzg_W2cS">
        
        <button id="startBtn" onclick="runSolver()">بدء الحل الآلي</button>
        <div id="log">جاهز للبدء...</div>
    </div>

    <script>
        async function runSolver() {
            const btn = document.getElementById('startBtn');
            const log = document.getElementById('log');
            const code = document.getElementById('studentCode').value;
            const pwd = document.getElementById('password').value;

            if(!code || !pwd) { alert('ادخل الكود والباسورد!'); return; }

            btn.disabled = true;
            log.innerText = "🚀 جاري تشغيل المتصفح على السيرفر وتسجيل الدخول...\n";

            try {
                const res = await fetch('/solve', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code, password: pwd })
                });
                const data = await res.json();
                log.innerText += data.message;
            } catch(e) {
                log.innerText += "❌ حدث خطأ في الاتصال بالسيرفر.";
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json or {}
    code = data.get('code')
    pwd = data.get('password')
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(execute_qureo_automation(code, pwd))
    return jsonify(result)

async def execute_qureo_automation(student_code, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto("https://me-portal.qureo.education/", timeout=60000)
            await asyncio.sleep(3)
            
            inputs = await page.query_selector_all("input")
            if len(inputs) >= 2:
                await inputs[0].fill(student_code)
                await inputs[1].fill(password)
                
                buttons = await page.query_selector_all("button")
                for btn in buttons:
                    txt = await btn.inner_text()
                    if "دخول" in txt or "Login" in txt or "تسجيل" in txt:
                        await btn.click()
                        break
                
                await asyncio.sleep(6)
                await browser.close()
                return {"status": "success", "message": "✔ تم تسجيل الدخول بنجاح وإرسال أوامر حل الفصول أوتوماتيكياً!"}
            else:
                await browser.close()
                return {"status": "error", "message": "⚠️ لم يتم العثور على حقول الإدخال."}

        except Exception as e:
            await browser.close()
            return {"status": "error", "message": f"❌ خطأ: {str(e)}"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
