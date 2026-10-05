import logging
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import pyautogui as py


BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "skils"
LOG_FILE = BASE_DIR / "bot.log"

CONFIDENCE = 0.7
INTERVALO_BUSCA = 0.2
INTERVALO_ENTRE_CICLOS = 0.5

HABILIDADES = tuple(f"skil{numero}.png" for numero in range(1, 8))
TELAS_FINAIS = (
    "continuar.png",
    "continuar1.png",
    "continuar2.png",
    "continuar3.png",
    *(f"x{numero}.png" for numero in range(3, 22)),
    "x23.png",
)
IMAGENS_OBRIGATORIAS = ("jugg.png", *HABILIDADES, *TELAS_FINAIS)

py.PAUSE = 0.08
py.FAILSAFE = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BotController:
    """Controla o ciclo do bot sem bloquear a interface grafica."""

    def __init__(self, eventos_ui):
        self._parar = threading.Event()
        self._thread = None
        self._eventos_ui = eventos_ui
        self._partidas = 0

    @property
    def executando(self):
        return self._thread is not None and self._thread.is_alive()

    def _notificar(self, tipo, valor):
        self._eventos_ui.put((tipo, valor))

    def _status(self, texto):
        logger.info(texto)
        self._notificar("status", texto)

    def iniciar(self):
        if self.executando:
            self._status("O bot ja esta em execucao.")
            return False

        ausentes = [nome for nome in IMAGENS_OBRIGATORIAS if not (IMAGES_DIR / nome).is_file()]
        if ausentes:
            logger.error("Imagens ausentes: %s", ", ".join(ausentes))
            self._notificar("imagens_ausentes", ausentes)
            return False

        self._parar.clear()
        self._thread = threading.Thread(
            target=self._executar,
            name="bot-jugg",
            daemon=True,
        )
        self._notificar("executando", True)
        self._thread.start()
        return True

    def parar(self):
        if not self.executando:
            self._notificar("executando", False)
            self._status("Bot parado.")
            return

        self._parar.set()
        self._status("Parando o bot...")

    def _esperar(self, segundos):
        """Espera com a possibilidade de interrupcao imediata."""
        return not self._parar.wait(segundos)

    def _localizar(self, nome):
        caminho = str(IMAGES_DIR / nome)
        try:
            return py.locateCenterOnScreen(
                caminho,
                confidence=CONFIDENCE,
                grayscale=True,
            )
        except Exception as erro:
            # Versoes recentes podem lancar ImageNotFoundException em vez de retornar None.
            if erro.__class__.__name__ == "ImageNotFoundException":
                return None
            raise

    def clicar_imagem(self, nome, timeout=1.0):
        """Clica apenas se a imagem for encontrada dentro do tempo limite."""
        limite = time.monotonic() + timeout

        while not self._parar.is_set() and time.monotonic() < limite:
            posicao = self._localizar(nome)
            if posicao is not None:
                py.click(posicao.x, posicao.y)
                logger.debug("Clique em %s na posicao %s", nome, posicao)
                return True

            if not self._esperar(INTERVALO_BUSCA):
                break

        return False

    def iniciar_jungle(self):
        self._status("Procurando uma partida Juggernaut...")
        encontrou = self.clicar_imagem("jugg.png", timeout=5.0)
        if encontrou:
            self._status("Partida encontrada. Aguardando a batalha...")
            self._esperar(1.0)
        return encontrou

    def usar_habilidades(self):
        self._status("Procurando habilidades disponiveis...")
        habilidades_usadas = 0

        for imagem in HABILIDADES:
            if self._parar.is_set():
                break
            if self.clicar_imagem(imagem, timeout=0.6):
                habilidades_usadas += 1

        logger.info("Habilidades usadas neste ciclo: %d", habilidades_usadas)
        return habilidades_usadas > 0

    def fechar_partida(self):
        self._status("Procurando telas de resultado...")
        fechou_alguma_tela = False

        for imagem in TELAS_FINAIS:
            if self._parar.is_set():
                break
            if self.clicar_imagem(imagem, timeout=0.5):
                fechou_alguma_tela = True
                self._esperar(0.3)

        if fechou_alguma_tela:
            self._partidas += 1
            self._notificar("partidas", self._partidas)

        return fechou_alguma_tela

    def _executar(self):
        erros_consecutivos = 0

        try:
            self._status("Bot iniciado.")
            while not self._parar.is_set():
                try:
                    iniciou = self.iniciar_jungle()
                    if iniciou and not self._parar.is_set():
                        self.usar_habilidades()
                        self.fechar_partida()

                    erros_consecutivos = 0
                    self._esperar(INTERVALO_ENTRE_CICLOS)
                except py.FailSafeException:
                    logger.warning("Fail-safe acionado pelo usuario.")
                    self._status("Fail-safe acionado. Bot interrompido.")
                    self._parar.set()
                except Exception:
                    erros_consecutivos += 1
                    logger.exception("Erro no ciclo do bot")
                    self._status(f"Erro no ciclo ({erros_consecutivos}). Tentando novamente...")

                    # Evita um loop acelerado de erros e para apos repetidas falhas.
                    if erros_consecutivos >= 5:
                        self._status("Muitos erros consecutivos. Bot interrompido.")
                        self._parar.set()
                    else:
                        self._esperar(1.0)
        finally:
            self._parar.set()
            self._notificar("executando", False)
            self._status("Bot parado.")


class BotApp:
    def __init__(self, janela):
        self.janela = janela
        self.eventos_ui = queue.Queue()
        self.controller = BotController(self.eventos_ui)

        janela.title("Bot Control")
        janela.geometry("440x280")
        janela.resizable(False, False)
        janela.configure(bg="#111827")
        janela.protocol("WM_DELETE_WINDOW", self.fechar)
        janela.bind("<F10>", lambda _evento: self.parar())

        self.status = tk.StringVar(value="Pronto para iniciar.")
        self.partidas = tk.StringVar(value="Partidas finalizadas: 0")

        tk.Label(
            janela,
            text="Bot Juggernaut",
            bg="#111827",
            fg="white",
            font=("Helvetica", 18, "bold"),
        ).pack(pady=(18, 8))

        tk.Label(
            janela,
            textvariable=self.status,
            bg="#111827",
            fg="#d1d5db",
            wraplength=400,
            font=("Helvetica", 10),
        ).pack(pady=6)

        tk.Label(
            janela,
            textvariable=self.partidas,
            bg="#111827",
            fg="#93c5fd",
            font=("Helvetica", 10, "bold"),
        ).pack(pady=4)

        estilo = {"width": 28, "height": 2, "fg": "white", "font": ("Helvetica", 11, "bold")}
        self.botao_comecar = tk.Button(
            janela,
            text="Start Bot",
            command=self.iniciar,
            bg="#2563eb",
            activebackground="#1d4ed8",
            **estilo,
        )
        self.botao_comecar.pack(pady=(10, 5))

        self.botao_parar = tk.Button(
            janela,
            text="Stop Bot (F10)",
            command=self.parar,
            bg="#dc2626",
            activebackground="#b91c1c",
            state=tk.DISABLED,
            **estilo,
        )
        self.botao_parar.pack(pady=5)

        self.janela.after(100, self.processar_eventos)

    def iniciar(self):
        self.status.set("Validando imagens...")
        self.controller.iniciar()

    def parar(self):
        self.controller.parar()

    def processar_eventos(self):
        try:
            while True:
                tipo, valor = self.eventos_ui.get_nowait()

                if tipo == "status":
                    self.status.set(valor)
                elif tipo == "partidas":
                    self.partidas.set(f"Partidas finalizadas: {valor}")
                elif tipo == "executando":
                    self.botao_comecar.configure(state=tk.DISABLED if valor else tk.NORMAL)
                    self.botao_parar.configure(state=tk.NORMAL if valor else tk.DISABLED)
                elif tipo == "imagens_ausentes":
                    self.status.set("Nao foi possivel iniciar: imagens ausentes.")
                    nomes = ", ".join(valor[:8])
                    complemento = f"\n... e mais {len(valor) - 8}." if len(valor) > 8 else ""
                    messagebox.showerror(
                        "Imagens ausentes",
                        f"Adicione as imagens na pasta:\n{IMAGES_DIR}\n\nAusentes: {nomes}{complemento}",
                    )
        except queue.Empty:
            pass

        self.janela.after(100, self.processar_eventos)

    def fechar(self):
        self.controller.parar()
        self.janela.destroy()


def main():
    janela = tk.Tk()
    BotApp(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()