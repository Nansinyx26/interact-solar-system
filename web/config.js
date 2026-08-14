/**
 * Constantes globais da versão web.
 *
 * Espelha o config.py do aplicativo desktop: escalas da cena, limiares de
 * detecção e parâmetros de animação. Nenhum outro módulo deve ter valor mágico.
 */

// ---------------------------------------------------------------------------
// Versão
// ---------------------------------------------------------------------------
// Uma única versão para as DUAS implementações (desktop e web). Ao alterar
// qualquer uma delas, suba este número aqui E em config.py — o
// verificar_paridade.py falha se os dois ficarem diferentes, e o publicar.py
// regenera o ZIP de download com a versão nova.
export const VERSAO = "1.3.1";

// Destino do botão "Baixar versão desktop".
//
// O pacote com o executável tem ~107 MB e o limite por arquivo estático do
// Vercel é 100 MB no plano Hobby — por isso ele NÃO é servido junto do site.
// Fica como asset de GitHub Releases (que aceita até 2 GB) e o botão aponta
// para lá. O caminho ".../releases/latest/download/..." resolve sempre para o
// release mais recente, então esta URL não precisa mudar a cada versão.
//
// Deixar vazio faz o botão servir o arquivo local gerado pelo empacotar_web.py
// (útil ao rodar o site localmente, onde não há limite de tamanho).
export const URL_DOWNLOAD_EXECUTAVEL =
  "https://github.com/Nansinyx26/interact-solar-system-exe/releases/latest/download/sistema-solar-gestos.zip";
export const ARQUIVO_DOWNLOAD_LOCAL = "sistema-solar-gestos.zip";
export const REPOSITORIO_GITHUB = "Nansinyx26/interact-solar-system-exe";

// ---------------------------------------------------------------------------
// Escalas da cena — ATENÇÃO: NÃO SÃO REALISTAS (e nem podem ser)
// ---------------------------------------------------------------------------
// Em escala linear real o Sistema Solar é indesenhável: se a órbita de Netuno
// (30,07 UA) coubesse na tela, Mercúrio (0,387 UA) ficaria a ~1% do raio, colado
// no Sol, e a Terra teria menos de 1 pixel. Usamos duas compressões:
//
// 1) RAIO ORBITAL — escala LOGARÍTMICA sobre ln(distância em UA).
// 2) RAIO DO CORPO — LEI DE POTÊNCIA com expoente 0,40.
// 3) O Sol tem raio FIXO, senão engoliria as primeiras órbitas.
//
// Os números reais, sem compressão, aparecem sempre na ficha do planeta.
export const RAIO_ORBITA_MIN_PX = 95;
export const RAIO_ORBITA_MAX_PX = 420;
export const RAIO_PLANETA_BASE_PX = 10;
export const EXPOENTE_RAIO_CORPO = 0.4;
export const RAIO_SOL_PX = 46;

// Altura de referência do enquadramento: o zoom escala junto com a janela.
export const ALTURA_REFERENCIA = 800;

// ---------------------------------------------------------------------------
// Tempo da simulação
// ---------------------------------------------------------------------------
// Quantos dias astronômicos passam por segundo real. Os períodos orbitais são
// proporcionais aos reais (Terra = referência).
export const TIME_SCALE = 12;
export const TIME_SCALE_MIN = 0.5;
export const TIME_SCALE_MAX = 400;
export const FATOR_AJUSTE_TEMPO = 1.5;
// Rotação própria comprimida: na proporção real Júpiter (9,93 h) seria um borrão.
export const FATOR_ROTACAO_PROPRIA = 0.06;

// ---------------------------------------------------------------------------
// Câmera
// ---------------------------------------------------------------------------
export const ZOOM_VISAO_GERAL = 0.9;
export const ZOOM_MIN = 0.35;
export const ZOOM_MAX = 6.0;
export const RAIO_ALVO_FOCO_PX = 92;
export const DURACAO_TRANSICAO_S = 0.8;
// Ao focar, o corpo é deslocado para a DIREITA: a ficha ocupa a coluna
// esquerda, então o alvo precisa fugir dela, não do lado oposto.
export const DESLOCAMENTO_FOCO_X_PX = 150;
export const FATOR_ZOOM_RODA = 1.15;

// ---------------------------------------------------------------------------
// Renderização
// ---------------------------------------------------------------------------
export const COR_FUNDO = "#060710";
export const COR_ORBITA = "78, 88, 120";
export const COR_ORBITA_FOCADA = "150, 200, 255";
export const ALPHA_ORBITA_NORMAL = 0.28;
export const ALPHA_ORBITA_TENUE = 0.09;
export const ALPHA_ORBITA_FOCADA = 0.75;
export const ALPHA_CORPO_ESMAECIDO = 0.28;

export const RAIO_TEXTURA_PX = 48;
export const QUADROS_ROTACAO = 24;
export const LARGURA_TIRA_EM_RAIOS = 4;
export const FAIXAS_GIGANTE_GASOSO = 9;
export const FAIXAS_ROCHOSO = 3;
export const ESCALA_RUIDO_TEXTURA = 10;
export const INTENSIDADE_TURBULENCIA = 2.6;
export const ALPHA_SOMBRA_MAX = 0.8;

export const CAMADAS_ESTRELAS = 3;
export const ESTRELAS_POR_CAMADA = 130;
export const FATOR_PARALLAX = [0.015, 0.045, 0.1];
export const SEMENTE_ALEATORIA = 20260813;

export const FATOR_ANEL_INTERNO = 1.35;
export const FATOR_ANEL_EXTERNO = 2.3;
export const ACHATAMENTO_ANEL = 0.28;
export const INCLINACAO_ANEL_GRAUS = -12;
export const COR_ANEL_SATURNO = "226, 206, 168";
export const FATOR_ANEL_URANO_INTERNO = 1.55;
export const FATOR_ANEL_URANO_EXTERNO = 1.8;
export const ACHATAMENTO_ANEL_URANO = 0.3;
export const INCLINACAO_ANEL_URANO_GRAUS = 82;
export const COR_ANEL_URANO = "176, 224, 230";
export const COMPRIMENTO_EIXO_URANO = 2.2;

export const FATOR_HALO_SOL = 3.2;
export const COR_ANEL_DESTAQUE = "140, 210, 255";
export const FOLGA_ANEL_DESTAQUE_PX = 14;

// ---------------------------------------------------------------------------
// Webcam e detecção de mãos
// ---------------------------------------------------------------------------
// Os artefatos do MediaPipe vêm do CDN por padrão. Para servir tudo do próprio
// domínio (deploy 100% offline), baixe os dois caminhos abaixo para web/vendor/
// e troque as constantes — o resto do código não muda.
export const URL_WASM_MEDIAPIPE =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm";
export const URL_MODELO_MAOS =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

export const MAX_MAOS = 2;
// Confiança baixa de propósito: 6, 7 e 8 exigem DUAS mãos, e a segunda costuma
// aparecer menor/mais inclinada. O filtro de verdade é a votação por maioria.
export const CONFIANCA_MIN_DETECCAO = 0.5;
export const CONFIANCA_MIN_PRESENCA = 0.5;
export const CONFIANCA_MIN_RASTREIO = 0.5;
// Detectar a cada N frames de render: a inferência custa ~10 ms e não precisa
// rodar a 60 Hz para uma confirmação que leva ~0,5 s.
export const DETECTAR_A_CADA_N_FRAMES = 2;

export const LARGURA_CAPTURA = 640;
export const ALTURA_CAPTURA = 480;

// O MediaPipe extrapola landmarks para fora de [0, 1] mesmo com a mão inteira
// visível; com margem apertada e duas mãos no quadro quase tudo era descartado
// e a contagem nunca passava de 5.
export const MARGEM_QUADRO = 0.06;
export const MAX_LANDMARKS_FORA_DO_QUADRO = 3;
export const LIMIAR_AVISO_CONFIANCA = 0.72;

// ---------------------------------------------------------------------------
// Contagem de dedos (limiares em frações do tamanho da palma)
// ---------------------------------------------------------------------------
export const LIMIAR_DEDO_ESTENDIDO = 0.16;
export const LIMIAR_POLEGAR_ESTENDIDO = 0.26;
export const MARGEM_ZONA_CINZENTA_POLEGAR = 0.1;
export const RAZAO_POLEGAR_ABERTO = 1.02;
export const TAMANHO_PALMA_MINIMO = 1e-4;

// ---------------------------------------------------------------------------
// Estabilização temporal do gesto
// ---------------------------------------------------------------------------
// O buffer guarda LEITURAS (inferências), não frames: ~15 leituras/s, então
// 10 leituras com maioria de 70% (7 votos) equivalem a ~0,5 s de gesto firme.
export const TAMANHO_BUFFER_GESTOS = 10;
export const FRACAO_MAIORIA = 0.7;
export const COOLDOWN_TROCA_S = 0.8;
export const SEGUNDOS_ATE_VISAO_GERAL = 6;

// Gesto de comando: as duas mãos abertas (5 + 5) reenquadram o sistema.
export const GESTO_VISAO_GERAL = 10;
// A partir daqui é impossível com uma mão só — é o que dispara a dica
// "use as duas mãos" no HUD quando a leitura chega em 5.
export const GESTO_MINIMO_DUAS_MAOS = 6;

// ---------------------------------------------------------------------------
// Luas dos demais planetas ("modo luas")
// ---------------------------------------------------------------------------
// Os gestos de 0 a 10 estão todos ocupados, então as luas menores não têm
// número próprio: aparecem em bloco quando o modo é ligado — pela tecla M ou
// pelo gesto das DUAS mãos em pinça, o único ainda livre.
// Ligadas por padrão: as luas são conteúdo, não um extra escondido atrás de
// um atalho. Na visão geral elas aparecem comprimidas (FATOR_LUA_COMPACTO_*).
export const LUAS_VISIVEIS_PADRAO = true;
// Raio desenhado de cada lua menor, em pixels de mundo. Fixo, como o da Lua: em
// proporção real Encélado (504 km) teria 0,2 px ao lado de Saturno.
export const RAIO_LUA_MENOR_PX = 2.2;
// Zoom a partir do qual as luas usam o raio orbital cheio. Abaixo dele o
// sistema é comprimido (ver FATOR_LUA_COMPACTO_*), não escondido.
export const ZOOM_MINIMO_PARA_LUAS = 1.6;

// Raio orbital COMPACTO, usado na visão geral — múltiplo do raio do planeta.
// Sem isso as luas invadem o planeta vizinho: em volta de Júpiter elas
// precisariam de 105 px e só há 70 px até Saturno. Com teto de 1,45 todo mundo
// cabe (Júpiter usa 38 px, a Lua da Terra usa 14,5 contra 34 de folga).
export const FATOR_LUA_COMPACTO_MIN = 1.15;
export const FATOR_LUA_COMPACTO_MAX = 1.45;
// Planetas com anéis precisam de um piso: com o fator compacto puro, as luas de
// Saturno cairiam DENTRO dos anéis, que vão até 2,3 raios.
export const FOLGA_LUA_APOS_ANEL = 0.15;
export const COR_ORBITA_LUA = "150, 160, 190";
export const ALPHA_ORBITA_LUA = 0.18;

// ---------------------------------------------------------------------------
// Cinturão de asteroides
// ---------------------------------------------------------------------------
// Fica entre Marte (1,52 UA) e Júpiter (5,20 UA). Como o raio orbital do
// projeto é logarítmico, a faixa é calculada em nucleo/orbita.js a partir
// destas distâncias reais.
export const CINTURAO_UA_INTERNO = 2.06;
export const CINTURAO_UA_EXTERNO = 3.27;
export const ASTEROIDES_DESENHADOS = 340;
export const COR_ASTEROIDE = "150, 138, 120";
export const ALPHA_ASTEROIDE_MIN = 0.24;
export const ALPHA_ASTEROIDE_MAX = 0.67;
// O cinturão gira devagar, como um corpo só: seguir o período real de cada
// asteroide não mudaria nada visualmente e custaria uma volta por partícula.
export const PERIODO_CINTURAO_DIAS = 1680.0;

// ---------------------------------------------------------------------------
// Gesto de pinça — zoom controlado pela câmera
// ---------------------------------------------------------------------------
// Distância ponta do polegar <-> ponta do indicador dividida pelo tamanho da
// palma, o que torna a medida independente da distância até a câmera.
//
// Histerese: entra em modo zoom abaixo de ATIVA e só sai acima de SAIDA. Com um
// limiar único a pinça piscaria na fronteira e o zoom entraria e sairia sozinho.
export const LIMIAR_PINCA_ATIVA = 0.38;
export const LIMIAR_PINCA_SAIDA = 0.55;
// Peso do valor novo na média móvel exponencial: sem filtro o zoom vibra com o
// tremor natural da mão.
export const SUAVIZACAO_PINCA = 0.35;
// Trava saltos quando o rastreio perde a mão por um instante.
export const FATOR_ZOOM_PINCA_MAX = 1.12;
// Sair da pinça passa por poses lidas como 1, 2 ou 3 dedos; sem esta pausa o
// zoom terminaria trocando de planeta.
export const COOLDOWN_APOS_PINCA_S = 0.6;

// ---------------------------------------------------------------------------
// Narração por voz (TTS)
// ---------------------------------------------------------------------------
export const NARRACAO_ATIVA_PADRAO = true;
export const IDIOMA_NARRACAO = "pt-BR";
// A Web Speech API usa 1 como velocidade natural; 175 ppm do pyttsx3 equivale a
// ~1,05 aqui. A constante compartilhada é a do desktop, convertida no narrador.
export const VELOCIDADE_NARRACAO = 175;
export const VOLUME_NARRACAO = 0.9;
// A narração lê a ficha inteira: nome, tipo, diâmetro, distância, períodos,
// luas, temperatura e o fato curioso. Desligado, fala só o nome e o tipo.
export const NARRAR_FICHA_COMPLETA = true;

// --- ElevenLabs (voz neural) ------------------------------------------------
// A chave da API JAMAIS pode chegar ao navegador: o front é público e qualquer
// visitante leria o valor. Por isso o site não fala com a ElevenLabs direto —
// ele chama /api/voz, uma função serverless que guarda a chave no ambiente do
// servidor (variável ELEVENLABS_API_KEY nas configurações do Vercel).
//
// Sem a função publicada (site aberto localmente, por exemplo) ou em caso de
// erro, o narrador cai para a voz do próprio navegador.
export const ENDPOINT_VOZ = "/api/voz";
export const ELEVENLABS_VOZ_NOME = "Brian";
// Servidor Backend no Render.com (para comunicação direta ou fallback entre Vercel e Render)
export const URL_SERVIDOR_RENDER = "https://sistema-solar-backend.onrender.com";


// ---------------------------------------------------------------------------
// Lua (satélite da Terra)
// ---------------------------------------------------------------------------
// Raio orbital da Lua em torno da Terra, em pixels de mundo. Não segue a escala
// logarítmica dos planetas — seria invisível. É um valor visual fixo.
export const RAIO_ORBITA_LUA_PX = 28;
// Raio desenhado da Lua (fixo, como o Sol). Em escala real seria ~0,27x a Terra,
// mas com raio base 10 px isso daria 2,7 px — pequeno demais para ver textura.
export const RAIO_LUA_PX = 4;

