Esse  é um símples bot de discord, que roda de maneira simples as músicas que estiverem salvas no seu armazenamento local, com direito a uma integração web, onde você pode mudar o volume, mudar de música e mais, tudo pela web, ou no celular caso esteja na mesma rede.

É simples e fácil pra usar esse bot, primeiro, cria um bot no site de desenvolvimento do discord, ativa as permissões e coloque-o no seu servidor.

Baixe o FFmpeg em:
https://www.gyan.dev/ffmpeg/builds/

Extraia o ZIP.

Dentro da pasta extraída tem bin/ffmpeg.exe.

Copie o caminho completo da pasta bin, tipo:
C:\Users\Nome\Downloads\ffmpeg\bin

Aperte Win + R, digite: sysdm.cpl
Vá em Avançado > Variáveis de Ambiente.
Na parte de baixo (Variáveis do Sistema), selecione Path e clique Editar.
Clique Novo e cole o caminho da pasta bin.
Dá OK em tudo e fecha.
Depois disso, abre um terminal novo e testa:
ffmpeg -version.

depois, na pasta do projeto, rode:

pip install -r requirements.txt


Crie uma pasta chamada "music" na mesma pasta que está o Soundbot.py.
Agora em Soundbot.py, no código, altere o Token do seu bot, e o IP do seu computador local e pronto, você já pode rodar soundbot.py usando:

python soundbot.py


Todas as músicas vão em music, de preferência no formato mp3, no discord, use /join pra fazer o bot entrar na sua chamada de voz, e ele ja está pronto pra tocar suas músicas.







Caso ocorra um erro onde o Bot sai e entra várias e várias vezes, tenha certeza que o seu bot não está sendo bloqueado pelo seu Firewall.

Como arrumar:

🚧 O problema (bem resumido)

Quando o bot conecta em call/voice, ele usa UDP pra enviar áudio.
Se o teu Windows ou roteador bloquear, ele faz isso:

Entra na call

Tenta mandar UDP

O firewall/roteador bloqueia

A conexão cai

O bot tenta reconnect

Fica num loop infinito igual NPC bugado

🎯 Como resolver (tutorial rápido)
1) Liberar o Python no Firewall

Vai no Windows:

Abre Painel de Controle

“Sistema e Segurança”

“Firewall do Windows Defender”

“Permitir um app pelo Firewall”

Acha python.exe na lista

Marca Privada e Pública

Se tiver mais de um python.exe → marca tudo

Se não aparecer:
Clica em “Permitir outro app” e adiciona o python na mão:

Normalmente fica em:

C:\Users\NOME\AppData\Local\Programs\Python\Python312\python.exe

2) Ativar Outbound + Inbound UDP

Ainda no firewall:

Vai em:

Configurações Avançadas > Regras de Entrada > Nova Regra


Cria:

Tipo: Porta

UDP

Porta específica: 50000-60000

Permitir conexão

Marca Domínio + Privada + Pública

Nome: DiscordBotUDP-IN

Repete o mesmo em Regras de Saída (Outbound):

Nome: DiscordBotUDP-OUT

Essas portas são usadas pelo Discord Voice.

3) Verificar NAT do roteador (opcional, mas salva a vida)

Se mesmo assim continuar caindo:

Entra no roteador

Habilita UPnP

Reinicia o roteador

Não usa VPN enquanto testa (VPN ama bloquear UDP)

4) Rodar PowerShell como Admin

Se estiver usando python bot.py, tenta rodar como admin pra garantir que o python consiga abrir portas UDP sem drama.

5) Anti-virus “CIUMENTO”

Se tu usa algum antivírus tipo Avast, BitDefender, Kaspersky… desconfia.
Eles bloqueiam UDP sem falar nada.

No antivírus:

Vai em “Proteção Web”

Adiciona python.exe como permitido.





Qualquer dúvida pode ser resolvida no meu discord: sungbro

ficarei feliz em responder qualquer dúvida


