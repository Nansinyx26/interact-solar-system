"""Narração por voz do corpo focado, usando o sintetizador do sistema.

Roda em **thread separada**: ``pyttsx3.say()`` + ``runAndWait()`` bloqueiam até a
fala terminar, e no loop de render isso congelaria a cena por segundos — o mesmo
motivo pelo qual a captura de vídeo já roda fora do laço principal.

A fila guarda no máximo um pedido: trocando de planeta rápido, o mais recente
substitui o anterior em vez de enfileirar uma narração que ninguém quer ouvir.

Sem o pyttsx3 instalado (ou sem voz no sistema) o narrador simplesmente fica
inativo — nada quebra, o aplicativo segue mudo.
"""

from __future__ import annotations

import io
import queue
import threading
from decimal import ROUND_HALF_UP, Decimal

import pygame

from config import (
    ELEVENLABS_VOZ_NOME,
    IDIOMA_NARRACAO,
    NARRACAO_ATIVA_PADRAO,
    NARRAR_FICHA_COMPLETA,
    VELOCIDADE_NARRACAO,
    VOLUME_NARRACAO,
)
from dados.planetas import CorpoCeleste
from ui.voz_elevenlabs import SinteseElevenLabs

try:  # pragma: no cover - depende do ambiente
    import pyttsx3

    PYTTSX3_DISPONIVEL = True
    ERRO_IMPORT_PYTTSX3 = ""
except ImportError as _erro:  # pragma: no cover
    pyttsx3 = None  # type: ignore[assignment]
    PYTTSX3_DISPONIVEL = False
    ERRO_IMPORT_PYTTSX3 = f"{type(_erro).__name__}: {_erro}"

# Sentinela que encerra a thread.
_PARAR = object()


# Artigo definido antes do nome. Em português corrente dizemos "o Sol" e "a
# Terra", mas "Marte" e "Júpiter" dispensam artigo.
ARTIGO_DEFINIDO: dict[str, str] = {"Sol": "O", "Terra": "A", "Lua": "A"}

# Descrição do tipo já com artigo indefinido, para a frase fechar concordância.
TIPO_NARRADO: dict[str, str] = {
    "estrela": "uma estrela",
    "rochoso": "um planeta rochoso",
    "gasoso": "um gigante gasoso",
    "satelite": "um satélite natural",
}


def _numero(valor: float, casas: int = 0) -> str:
    """Número no padrão pt-BR, que é como o sintetizador lê corretamente.

    Arredonda com ROUND_HALF_UP para bater com o ``Intl.NumberFormat`` da versão
    web. O padrão do Python é half-even ("banker's rounding"), que em empates
    exatos discorda do JavaScript: a rotação de Mercúrio (58,65 dias) virava
    58,6 aqui e 58,7 lá — o verificador de paridade pegou a diferença.
    """
    arredondado = Decimal(str(valor)).quantize(
        Decimal(1) if casas == 0 else Decimal("0." + "0" * casas),
        rounding=ROUND_HALF_UP,
    )
    texto = f"{arredondado:,.{casas}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def frases_da_ficha(corpo: CorpoCeleste) -> list[str]:
    """A ficha do corpo em orações completas, prontas para serem lidas.

    É a mesma informação do card, dita em português corrente: "Tem 12.756
    quilômetros de diâmetro" em vez de "Diâmetro equatorial: 12.756 km". Rótulo
    e valor soltos soariam como uma planilha sendo lida em voz alta.
    """
    frases = [f"Tem {_numero(corpo.diametro_km)} quilômetros de diâmetro."]

    if corpo.eh_satelite:
        frases.append(
            f"Fica a {_numero(corpo.distancia_km)} quilômetros "
            f"{'da' if corpo.orbita_em_torno_de == 'Terra' else 'de'} "
            f"{corpo.orbita_em_torno_de}."
        )
    elif corpo.distancia_ua > 0:
        frases.append(
            f"Fica a {_numero(corpo.distancia_ua, 2)} unidades astronômicas do Sol, "
            f"ou seja, {_numero(corpo.distancia_km)} quilômetros."
        )

    if corpo.periodo_orbital_dias > 0:
        if corpo.periodo_orbital_dias >= 365.26:
            anos = corpo.periodo_orbital_dias / 365.26
            frases.append(f"Uma volta completa leva {_numero(anos, 1)} anos terrestres.")
        else:
            frases.append(
                f"Uma volta completa leva {_numero(corpo.periodo_orbital_dias)} dias."
            )

    horas = abs(corpo.periodo_rotacao_horas)
    sentido = " no sentido contrário ao dos demais" if corpo.periodo_rotacao_horas < 0 else ""
    if horas >= 48:
        frases.append(f"Gira em torno de si mesmo em {_numero(horas / 24, 1)} dias{sentido}.")
    else:
        frases.append(f"Gira em torno de si mesmo em {_numero(horas, 1)} horas{sentido}.")

    if corpo.luas == 1:
        frases.append("Tem uma lua conhecida.")
    elif corpo.luas > 1:
        frases.append(f"Tem {_numero(corpo.luas)} luas conhecidas.")

    frases.append(
        f"A temperatura média é de {_numero(corpo.temperatura_media_c)} graus Celsius."
    )
    frases.append(corpo.fato_curioso)
    return frases


def texto_do_corpo(corpo: CorpoCeleste) -> str:
    """Texto narrado ao focar um corpo.

    A abertura é uma **oração completa** ("A Terra é um planeta rochoso.") e não
    uma lista de termos ("Terra. Planeta rochoso"). O motivo é prático: o modelo
    de voz identifica o idioma pelo texto, e nomes latinos soltos são ambíguos —
    medindo com a transcrição da própria ElevenLabs, "Sol. Estrela" saía em
    espanhol e "Marte. Planeta rochoso" em inglês. O verbo "é" acentuado e os
    artigos são o que ancora a frase no português.
    """
    artigo = ARTIGO_DEFINIDO.get(corpo.nome)
    sujeito = f"{artigo} {corpo.nome}" if artigo else corpo.nome
    descricao = TIPO_NARRADO.get(corpo.tipo, "um corpo celeste")
    partes = [f"{sujeito} é {descricao}."]
    if NARRAR_FICHA_COMPLETA:
        partes.extend(frases_da_ficha(corpo))
    return " ".join(partes)


class Narrador:
    """Fala frases curtas sem bloquear o loop de render."""

    def __init__(self, ativo: bool = NARRACAO_ATIVA_PADRAO) -> None:
        # Voz neural primeiro, voz do sistema como rede de proteção: qualquer
        # uma das duas já torna a narração possível.
        self._neural = SinteseElevenLabs()
        self.disponivel = PYTTSX3_DISPONIVEL or self._neural.disponivel
        self.ativo = ativo and self.disponivel
        self.mensagem = "" if self.disponivel else "TTS indisponível"
        self._fila: queue.Queue = queue.Queue(maxsize=1)
        self._thread: threading.Thread | None = None
        self._encerrando = threading.Event()

    # ------------------------------------------------------------- ciclo
    def iniciar(self) -> None:
        """Sobe a thread de fala (não faz nada se o TTS não existe)."""
        # Qual voz está em uso é a primeira dúvida quando a narração "não
        # funciona": o log evita ter que adivinhar.
        if self._neural.disponivel:
            print(
                f"[narrador] voz neural {ELEVENLABS_VOZ_NOME} (ElevenLabs) ativa",
                flush=True,
            )
        else:
            print(f"[narrador] ElevenLabs fora: {self._neural.mensagem}", flush=True)
            print(
                f"[narrador] voz local do sistema "
                f"{'disponível' if PYTTSX3_DISPONIVEL else 'INDISPONÍVEL'}"
                f"{'' if PYTTSX3_DISPONIVEL else f' ({ERRO_IMPORT_PYTTSX3})'}",
                flush=True,
            )
        if not self.disponivel or self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._laco, name="narrador", daemon=True
        )
        self._thread.start()

    def parar(self) -> None:
        """Encerra a thread, aguardando a fala em andamento terminar."""
        self._encerrando.set()
        if self._thread is None:
            return
        self._descartar_pendente()
        try:
            self._fila.put_nowait(_PARAR)
        except queue.Full:
            pass
        self._thread.join(timeout=3.0)
        self._thread = None

    def alternar(self) -> bool:
        """Liga/desliga a narração e devolve o novo estado."""
        if not self.disponivel:
            return False
        self.ativo = not self.ativo
        if not self.ativo:
            self._descartar_pendente()
        return self.ativo

    # ------------------------------------------------------------ pedidos
    def anunciar(self, texto: str) -> None:
        """Coloca uma frase na fila, substituindo a que estiver esperando."""
        if not self.ativo or self._thread is None:
            return
        self._descartar_pendente()
        try:
            self._fila.put_nowait(texto)
        except queue.Full:  # corrida com a thread: a fala atual já basta
            pass

    def _descartar_pendente(self) -> None:
        """Esvazia a fila para o pedido novo não entrar atrás de um velho."""
        while True:
            try:
                self._fila.get_nowait()
            except queue.Empty:
                return

    # --------------------------------------------------------------- thread
    def _laco(self) -> None:
        """Consome a fila falando uma frase por vez.

        Dois caminhos: a voz neural da ElevenLabs (melhor resultado, precisa de
        chave e rede) e a voz local do sistema. O segundo é o que garante que o
        aplicativo continue completo offline.
        """
        motor = self._criar_motor()
        if motor is None and not self._neural.disponivel:
            self.ativo = False
            self.disponivel = False
            return
        try:
            while not self._encerrando.is_set():
                try:
                    item = self._fila.get(timeout=0.2)
                except queue.Empty:
                    continue
                if item is _PARAR:
                    return
                if self._falar_neural(item):
                    continue
                if motor is None:
                    continue
                try:
                    motor.say(item)
                    motor.runAndWait()
                except RuntimeError:
                    # runAndWait reentrante ou motor derrubado pelo driver:
                    # perder uma fala é melhor que derrubar a thread.
                    continue
        finally:
            if motor is not None:
                try:
                    motor.stop()
                except Exception:  # noqa: BLE001 - encerramento não pode falhar
                    pass

    def _falar_neural(self, texto: str) -> bool:
        """Toca a frase com a voz da ElevenLabs. False = usar a voz local."""
        if not self._neural.disponivel:
            return False
        dados = self._neural.audio(texto)
        if not dados:
            return False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            # music (e não Sound) porque o retorno é MP3 e precisamos poder
            # cortar a fala anterior ao trocar de planeta.
            pygame.mixer.music.load(io.BytesIO(dados), "mp3")
            pygame.mixer.music.set_volume(VOLUME_NARRACAO)
            pygame.mixer.music.play()
        except pygame.error as erro:
            print(f"[narrador] falha ao tocar o áudio: {erro}", flush=True)
            return False

        # Espera a fala terminar, mas acordando com frequência: um pedido novo
        # na fila deve interromper a narração atual, não entrar atrás dela.
        while pygame.mixer.music.get_busy() and not self._encerrando.is_set():
            if not self._fila.empty():
                pygame.mixer.music.stop()
                break
            pygame.time.wait(50)
        return True

    def _criar_motor(self):
        """Instancia o pyttsx3 e escolhe a voz do idioma configurado."""
        if not PYTTSX3_DISPONIVEL:
            return None
        try:
            motor = pyttsx3.init()
        except Exception as erro:  # noqa: BLE001 - driver de TTS varia por SO
            self.mensagem = f"TTS indisponível: {erro}"
            print(f"[narrador] {self.mensagem}", flush=True)
            return None

        motor.setProperty("rate", VELOCIDADE_NARRACAO)
        motor.setProperty("volume", VOLUME_NARRACAO)
        voz = self._escolher_voz(motor)
        if voz is not None:
            motor.setProperty("voice", voz)
        else:
            print(
                f"[narrador] sem voz {IDIOMA_NARRACAO} instalada — usando a padrão",
                flush=True,
            )
        return motor

    @staticmethod
    def _escolher_voz(motor) -> str | None:
        """Procura uma voz do idioma configurado entre as instaladas."""
        alvo = IDIOMA_NARRACAO.lower()
        curto = alvo.split("-")[0]
        try:
            vozes = motor.getProperty("voices")
        except Exception:  # noqa: BLE001
            return None
        for voz in vozes:
            idiomas = [
                item.decode(errors="ignore") if isinstance(item, bytes) else str(item)
                for item in getattr(voz, "languages", []) or []
            ]
            texto = " ".join([voz.id, getattr(voz, "name", ""), *idiomas]).lower()
            if alvo in texto or f"_{curto}-" in texto or f" {curto} " in texto:
                return voz.id
        return None
