// AmparaPet — Painel de controle (Windows Forms, .NET Framework 4, C# 5).
// Substitui os .bat com uma janela: ligar/desligar, abrir o site, testes, console SQL.
// Por baixo chama os mesmos scripts de scripts\*.ps1 usados pelos .bat.
// Compilar: powershell -ExecutionPolicy Bypass -File scripts\compilar_painel.ps1
using System;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AmparaPet
{
    static class Programa
    {
        [DllImport("user32.dll")]
        static extern bool SetProcessDPIAware();

        [STAThread]
        static void Main()
        {
            bool primeiro;
            using (var trava = new Mutex(true, "AmparaPet.Painel", out primeiro))
            {
                if (!primeiro)
                {
                    MessageBox.Show("O painel do AmparaPet já está aberto.", "AmparaPet",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }
                try { SetProcessDPIAware(); } catch { }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new Painel());
            }
        }
    }

    class Painel : Form
    {
        const int PortaApi = 8000, PortaBanco = 3307;
        const string UrlSite = "http://localhost:8000/teste/";
        const string UrlDocs = "http://localhost:8000/docs";

        static readonly Color Azul = Color.FromArgb(43, 74, 111);
        static readonly Color Verde = Color.FromArgb(34, 139, 74);
        static readonly Color Cinza = Color.FromArgb(120, 128, 140);
        static readonly Color Laranja = Color.FromArgb(200, 120, 20);

        readonly string raiz = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
        readonly Label lblBanco = new Label(), lblApi = new Label(), lblAtividade = new Label();
        readonly TextBox log = new TextBox();
        readonly CheckBox chkNavegador = new CheckBox();
        readonly System.Windows.Forms.Timer timerStatus = new System.Windows.Forms.Timer();
        readonly System.Windows.Forms.Timer timerLogApi = new System.Windows.Forms.Timer();
        Button btnIniciar, btnParar, btnSite, btnDocs, btnTestes, btnConsole, btnBibliotecas;
        Control[] botoesDeAcao;

        bool ocupado, bancoLigado, apiLigada, fechando, verificando;
        long posicaoLogApi;

        string Caminho(string relativo) { return Path.Combine(raiz, relativo); }
        string ArquivoLogApi { get { return Caminho(@"logs\api.log"); } }

        public Painel()
        {
            Text = "AmparaPet — Painel de controle";
            Font = new Font("Segoe UI", 10F);
            AutoScaleMode = AutoScaleMode.Dpi;
            AutoScaleDimensions = new SizeF(96F, 96F);
            ClientSize = new Size(860, 640);
            MinimumSize = new Size(760, 560);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Color.FromArgb(245, 247, 250);
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

            MontarTela();

            timerStatus.Interval = 1500;
            timerStatus.Tick += delegate { AtualizarStatus(); };
            timerLogApi.Interval = 700;
            timerLogApi.Tick += delegate { LerLogApi(); };

            Load += delegate
            {
                if (!File.Exists(Caminho(@"scripts\banco.ps1")))
                {
                    MessageBox.Show("Não encontrei os arquivos do projeto.\n\nO AmparaPet.exe precisa ficar na pasta " +
                        "principal do projeto (junto do iniciar.bat).", "AmparaPet", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    Close();
                    return;
                }
                Escrever("Painel aberto. Pasta do projeto: " + raiz);
                Escrever("Clique em \"Iniciar\" para ligar o banco de dados e a API.");
                AtualizarStatus();
                timerStatus.Start();
                timerLogApi.Start();
            };
            FormClosing += AoFechar;
        }

        // ---------------------------------------------------------------- tela

        void MontarTela()
        {
            var cabecalho = new Panel { Dock = DockStyle.Top, Height = 74, BackColor = Azul };
            var titulo = new Label
            {
                Text = "AmparaPet", ForeColor = Color.White, AutoSize = true,
                Font = new Font("Segoe UI Semibold", 18F), Location = new Point(18, 8)
            };
            var subtitulo = new Label
            {
                Text = "Painel de controle do sistema de adoção — Abrigo Toca de Assis",
                ForeColor = Color.FromArgb(210, 222, 236), AutoSize = true, Location = new Point(21, 46)
            };
            cabecalho.Controls.Add(titulo);
            cabecalho.Controls.Add(subtitulo);

            var corpo = new TableLayoutPanel
            {
                Dock = DockStyle.Fill, Padding = new Padding(14, 10, 14, 14), ColumnCount = 1, RowCount = 5
            };
            corpo.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            corpo.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            corpo.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            corpo.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            corpo.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));

            // Situação
            var status = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 2, Margin = new Padding(0, 0, 0, 8) };
            status.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
            status.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
            status.Controls.Add(Cartao("Banco de dados (MySQL, porta 3307)", lblBanco), 0, 0);
            status.Controls.Add(Cartao("API / site (http://localhost:8000)", lblApi), 1, 0);
            corpo.Controls.Add(status, 0, 0);

            // Ações principais
            btnIniciar = Botao("▶  Iniciar", Verde, Color.White, 170, delegate { Iniciar(); });
            btnParar = Botao("■  Parar", Color.FromArgb(180, 50, 50), Color.White, 170, delegate { Parar(); });
            btnSite = Botao("Abrir site de teste", Color.White, Azul, 180, delegate { AbrirUrl(UrlSite); });
            btnDocs = Botao("Documentação da API", Color.White, Azul, 190, delegate { AbrirUrl(UrlDocs); });
            btnIniciar.Font = btnParar.Font = new Font("Segoe UI Semibold", 11F);
            chkNavegador.Text = "Abrir o navegador ao iniciar";
            chkNavegador.Checked = true;
            chkNavegador.AutoSize = true;
            chkNavegador.Margin = new Padding(8, 14, 0, 0);
            corpo.Controls.Add(Grupo("Sistema", btnIniciar, btnParar, btnSite, btnDocs, chkNavegador), 0, 1);

            // Ferramentas
            btnTestes = Botao("Rodar testes", Color.White, Azul, 150, delegate { RodarTestes(); });
            btnConsole = Botao("Console do MySQL", Color.White, Azul, 170, delegate { AbrirConsole(); });
            btnBibliotecas = Botao("Reinstalar bibliotecas", Color.White, Azul, 190, delegate { ReinstalarBibliotecas(); });
            var btnPasta = Botao("Abrir pasta", Color.White, Azul, 120, delegate { Process.Start("explorer.exe", "\"" + raiz + "\""); });
            var btnLogBanco = Botao("Log do MySQL", Color.White, Azul, 140, delegate { AbrirArquivo(@"mysql\mysql.log"); });
            corpo.Controls.Add(Grupo("Ferramentas", btnTestes, btnConsole, btnBibliotecas, btnPasta, btnLogBanco), 0, 2);

            botoesDeAcao = new Control[] { btnIniciar, btnParar, btnTestes, btnConsole, btnBibliotecas };

            lblAtividade.AutoSize = true;
            lblAtividade.ForeColor = Laranja;
            lblAtividade.Margin = new Padding(2, 6, 0, 4);
            corpo.Controls.Add(lblAtividade, 0, 3);

            // Registro
            log.Multiline = true;
            log.ReadOnly = true;
            log.ScrollBars = ScrollBars.Vertical;
            log.WordWrap = true;
            log.Dock = DockStyle.Fill;
            log.Font = new Font("Consolas", 9.5F);
            log.BackColor = Color.FromArgb(28, 33, 40);
            log.ForeColor = Color.FromArgb(220, 226, 232);
            log.BorderStyle = BorderStyle.None;
            var moldura = new GroupBox { Text = "Registro", Dock = DockStyle.Fill, Padding = new Padding(8) };
            moldura.Controls.Add(log);
            corpo.Controls.Add(moldura, 0, 4);

            Controls.Add(corpo);
            Controls.Add(cabecalho);
        }

        Control Cartao(string titulo, Label valor)
        {
            var p = new Panel { Dock = DockStyle.Fill, Height = 70, BackColor = Color.White, Margin = new Padding(0, 0, 8, 0) };
            p.Paint += delegate(object s, PaintEventArgs e)
            {
                e.Graphics.DrawRectangle(new Pen(Color.FromArgb(205, 213, 222)), 0, 0, p.Width - 1, p.Height - 1);
            };
            var t = new Label { Text = titulo, AutoSize = true, ForeColor = Cinza, Location = new Point(12, 8) };
            valor.AutoSize = true;
            valor.Font = new Font("Segoe UI Semibold", 13F);
            valor.Location = new Point(10, 32);
            valor.Text = "…";
            p.Controls.Add(t);
            p.Controls.Add(valor);
            return p;
        }

        GroupBox Grupo(string titulo, params Control[] filhos)
        {
            var g = new GroupBox { Text = titulo, Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8, 4, 8, 8), Margin = new Padding(0, 0, 0, 6) };
            var f = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoSize = true, WrapContents = true };
            f.Controls.AddRange(filhos);
            g.Controls.Add(f);
            return g;
        }

        Button Botao(string texto, Color fundo, Color letra, int largura, EventHandler acao)
        {
            var b = new Button
            {
                Text = texto, BackColor = fundo, ForeColor = letra, Width = largura, Height = 40,
                FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand, Margin = new Padding(4)
            };
            b.FlatAppearance.BorderColor = fundo == Color.White ? Color.FromArgb(180, 192, 206) : fundo;
            b.Click += acao;
            return b;
        }

        // ------------------------------------------------------------ registro

        void Escrever(string texto)
        {
            if (InvokeRequired) { BeginInvoke(new Action<string>(Escrever), texto); return; }
            if (log.TextLength > 200000) log.Text = log.Text.Substring(100000);
            log.AppendText(DateTime.Now.ToString("HH:mm:ss") + "  " + texto + Environment.NewLine);
        }

        void Atividade(string texto)
        {
            if (InvokeRequired) { BeginInvoke(new Action<string>(Atividade), texto); return; }
            lblAtividade.Text = texto;
        }

        // Mostra no registro o que a API escreve em logs\api.log
        void LerLogApi()
        {
            try
            {
                if (!File.Exists(ArquivoLogApi)) return;
                using (var fs = new FileStream(ArquivoLogApi, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
                {
                    if (fs.Length < posicaoLogApi) posicaoLogApi = 0;
                    if (fs.Length == posicaoLogApi) return;
                    fs.Seek(posicaoLogApi, SeekOrigin.Begin);
                    var leitor = new StreamReader(fs, Encoding.UTF8);
                    var novo = leitor.ReadToEnd();
                    posicaoLogApi = fs.Length;
                    foreach (var linha in novo.Split('\n'))
                        if (linha.Trim().Length > 0) Escrever("[API] " + linha.TrimEnd('\r'));
                }
            }
            catch (IOException) { }
        }

        // -------------------------------------------------------------- status

        static bool PortaAberta(int porta)
        {
            using (var c = new TcpClient())
            {
                try
                {
                    var r = c.BeginConnect("127.0.0.1", porta, null, null);
                    return r.AsyncWaitHandle.WaitOne(250) && c.Connected;
                }
                catch { return false; }
            }
        }

        async void AtualizarStatus()
        {
            if (verificando) return;
            verificando = true;
            try
            {
                bancoLigado = await Task.Run(() => PortaAberta(PortaBanco));
                apiLigada = await Task.Run(() => PortaAberta(PortaApi));
            }
            finally { verificando = false; }
            Mostrar(lblBanco, bancoLigado);
            if (!(ocupado && lblApi.Text.StartsWith("● Iniciando"))) Mostrar(lblApi, apiLigada);
            btnSite.Enabled = btnDocs.Enabled = apiLigada;
        }

        static void Mostrar(Label l, bool ligado)
        {
            l.Text = ligado ? "● Ligado" : "● Desligado";
            l.ForeColor = ligado ? Verde : Cinza;
        }

        void Ocupado(bool sim, string texto)
        {
            ocupado = sim;
            foreach (var b in botoesDeAcao) b.Enabled = !sim;
            Atividade(sim ? "⏳ " + texto : "");
            UseWaitCursor = sim;
        }

        // ------------------------------------------------- execução de scripts

        // Roda um processo escondido e manda a saída para o registro. Devolve o código de saída.
        int Rodar(string exe, string argumentos, string pasta, Encoding codificacao)
        {
            var info = new ProcessStartInfo(exe, argumentos)
            {
                WorkingDirectory = pasta, UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true,
                StandardOutputEncoding = codificacao, StandardErrorEncoding = codificacao
            };
            info.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            using (var p = new Process { StartInfo = info })
            {
                p.OutputDataReceived += (s, e) => { if (!string.IsNullOrEmpty(e.Data)) Escrever(e.Data); };
                p.ErrorDataReceived += (s, e) => { if (!string.IsNullOrEmpty(e.Data)) Escrever(e.Data); };
                p.Start();
                p.BeginOutputReadLine();
                p.BeginErrorReadLine();
                p.WaitForExit();
                return p.ExitCode;
            }
        }

        // O PowerShell 5.1 escreve na codificação OEM do console quando a saída é redirecionada
        int Script(string nome, string argumentos)
        {
            var oem = Encoding.GetEncoding(CultureInfo.CurrentCulture.TextInfo.OEMCodePage);
            return Rodar("powershell.exe",
                "-NoProfile -ExecutionPolicy Bypass -File \"" + Caminho(@"scripts\" + nome) + "\" " + argumentos,
                raiz, oem);
        }

        int Python(string argumentos)
        {
            return Rodar(Caminho(@"python\python.exe"), argumentos, Caminho("backend"), Encoding.UTF8);
        }

        // ---------------------------------------------------------------- ações

        async void Iniciar()
        {
            if (ocupado) return;
            if (apiLigada && bancoLigado)
            {
                Escrever("O sistema já está ligado.");
                if (chkNavegador.Checked) AbrirUrl(UrlSite);
                return;
            }
            Ocupado(true, "Iniciando o sistema…");
            lblApi.Text = "● Iniciando…";
            lblApi.ForeColor = Laranja;
            bool ok = await Task.Run(() => IniciarTudo());
            Ocupado(false, null);
            AtualizarStatus();
            if (ok)
            {
                Escrever("Pronto! Sistema ligado em " + UrlSite);
                if (chkNavegador.Checked) AbrirUrl(UrlSite);
            }
            else
            {
                Escrever("Não foi possível iniciar. Veja as mensagens acima.");
                MessageBox.Show(this, "Não foi possível iniciar o sistema.\nVeja o motivo no registro do painel.",
                    "AmparaPet", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        bool IniciarTudo()
        {
            if (!PortaAberta(PortaApi))
            {
                Escrever("Verificando o computador…");
                if (Script("preparar.ps1", "") != 0) return false;
            }
            Escrever("Verificando o Python portátil…");
            if (Script("python.ps1", "preparar") != 0) return false;
            if (!File.Exists(Caminho(".env")) && File.Exists(Caminho(".env.example")))
                File.Copy(Caminho(".env.example"), Caminho(".env"));

            Escrever("Ligando o banco de dados…");
            if (Script("banco.ps1", "iniciar") != 0) return false;

            if (PortaAberta(PortaApi)) return true;
            Escrever("Ligando a API…");
            return LigarApi();
        }

        bool LigarApi()
        {
            Directory.CreateDirectory(Caminho("logs"));
            posicaoLogApi = 0;
            // A saída vai para um arquivo (e não direto para o painel) para a API continuar
            // funcionando mesmo se o painel for fechado sem desligar o sistema.
            var comando = "/s /c \"\"" + Caminho(@"python\python.exe") + "\" -m uvicorn app.main:app " +
                "--host 127.0.0.1 --port " + PortaApi + " > \"" + ArquivoLogApi + "\" 2>&1\"";
            var info = new ProcessStartInfo("cmd.exe", comando)
            {
                WorkingDirectory = Caminho("backend"), UseShellExecute = false, CreateNoWindow = true
            };
            info.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            info.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            var processo = Process.Start(info);

            for (int i = 0; i < 80; i++)  // até ~40 s
            {
                if (PortaAberta(PortaApi)) return true;
                if (processo.HasExited)
                {
                    Thread.Sleep(300);
                    Escrever("A API fechou logo ao iniciar (código " + processo.ExitCode + ").");
                    return false;
                }
                Thread.Sleep(500);
            }
            Escrever("A API demorou demais para responder.");
            return false;
        }

        async void Parar()
        {
            if (ocupado) return;
            Ocupado(true, "Desligando o sistema…");
            await Task.Run(() => PararTudo());
            Ocupado(false, null);
            AtualizarStatus();
        }

        void PararTudo()
        {
            Escrever("Desligando a API…");
            Script("api.ps1", "parar");
            Escrever("Desligando o banco de dados…");
            Script("banco.ps1", "parar");
            Escrever("Sistema desligado.");
        }

        async void RodarTestes()
        {
            if (ocupado) return;
            Ocupado(true, "Rodando os testes automatizados…");
            int codigo = await Task.Run(() =>
            {
                if (Script("python.ps1", "preparar") != 0) return 1;
                if (Script("banco.ps1", "iniciar") != 0) return 1;
                Escrever("Rodando os testes (banco separado amparapet_teste; os dados reais não são tocados)…");
                return Python("-m pytest -q -p no:warnings -p no:cacheprovider");
            });
            Ocupado(false, null);
            AtualizarStatus();
            Escrever(codigo == 0 ? "Todos os testes passaram." : "Algum teste falhou. Veja acima.");
        }

        async void AbrirConsole()
        {
            if (ocupado) return;
            Ocupado(true, "Ligando o banco para abrir o console…");
            int codigo = await Task.Run(() => Script("banco.ps1", "iniciar"));
            Ocupado(false, null);
            AtualizarStatus();
            if (codigo != 0) return;
            Escrever("Console do MySQL aberto em outra janela. Digite exit para sair.");
            Process.Start(new ProcessStartInfo("powershell.exe",
                "-NoProfile -ExecutionPolicy Bypass -File \"" + Caminho(@"scripts\banco.ps1") + "\" console")
            { UseShellExecute = true, WorkingDirectory = raiz });
        }

        async void ReinstalarBibliotecas()
        {
            if (ocupado) return;
            if (MessageBox.Show(this, "Reinstalar as bibliotecas do Python?\nIsso precisa de internet e leva cerca de 1 minuto.",
                "AmparaPet", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            Ocupado(true, "Reinstalando as bibliotecas…");
            int codigo = await Task.Run(() => Script("python.ps1", "dependencias"));
            Ocupado(false, null);
            Escrever(codigo == 0 ? "Bibliotecas reinstaladas." : "Falha ao reinstalar as bibliotecas.");
        }

        void AbrirUrl(string url)
        {
            try { Process.Start(url); }
            catch (Exception ex) { Escrever("Não consegui abrir o navegador: " + ex.Message); }
        }

        void AbrirArquivo(string relativo)
        {
            var arq = Caminho(relativo);
            if (!File.Exists(arq)) { Escrever("Arquivo ainda não existe: " + relativo); return; }
            Process.Start("notepad.exe", "\"" + arq + "\"");
        }

        // ------------------------------------------------------------- fechar

        async void AoFechar(object sender, FormClosingEventArgs e)
        {
            if (fechando) return;
            if (ocupado)
            {
                e.Cancel = true;
                MessageBox.Show(this, "Aguarde a operação atual terminar.", "AmparaPet");
                return;
            }
            if (!bancoLigado && !apiLigada) return;

            var r = MessageBox.Show(this,
                "O sistema ainda está ligado.\n\nDeseja desligar o banco de dados e a API antes de sair?\n\n" +
                "Sim: desliga tudo e fecha.\nNão: fecha só o painel (o sistema continua ligado).",
                "AmparaPet", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question);
            if (r == DialogResult.Cancel) { e.Cancel = true; return; }
            if (r == DialogResult.No) return;

            e.Cancel = true;
            Ocupado(true, "Desligando o sistema…");
            await Task.Run(() => PararTudo());
            fechando = true;
            Close();
        }
    }
}
