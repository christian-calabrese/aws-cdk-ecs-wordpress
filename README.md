# WordPress highly available su AWS
___
## 1. Guida per lo sviluppatore
Lo IaC è stato sviluppato con AWS CDK in Python.
Sul repository git è stato utilizzato git flow per una migliore gestione dei branch.

L'architettura può essere deployata su diversi ambienti con parametri diversi.
I file di parametri (in json) sono contenuti nella cartella `/infrastructure/parameters` ed è scelto a runtime tramite variabile d'ambiente `ENVIRONMENT`.

Il repository è suddiviso in questo modo:
```
root
│   README.md
│   app.py - Lo script entrypoint di CDK
│
└───infrastructure
│   │   infrastructure_stack.py - Lo stack principale della architettura
│   │
│   └───parameters - La cartella che contiene i parametri di ogni ambiente
│   │    │   dev.json
│   │    │   prod.json
│   │
│   └───stacks - La cartella che contiene il codice dei nested stack
│   │    │   vpc_stack.py
│   │    │   database_stack.py
│   │    │   fargate_stack.py
│   │    │   pipeline_stack.py
│   │
│   └───utils - Una cartella con alcuni utility script necessari
└───images
    │
    └───wordpress - La cartella che contiene i file necessari alla creazione della Docker image
         │   Dockerfile
         │   wp-config.php - Nel file wp-config.php è possibile installare plugin di wordpress e gestire le sue impostazioni
```

### Installazione requisiti
1. Installa (https://www.python.org/downloads/)
2. Installa node.js (https://nodejs.org/en/download/)
3. Installa la dipendenza npm di CDK con `npm i -g aws-cdk`
4. Attiva il Python virtual environment per evitare di sporcare l'ambiente globale
   1. Windows `.\.venv\bin\activate`
   2. Unix `source .venv/bin/activate`
5. Installa le dipendenze Python `pip3 install -r requirements.txt`
6. Imposta la variabile d'ambiente ENVIRONMENT a dev o prod in base all'ambiente da deployare
7. Deploya l'infrastruttura tramite `cdk deploy`

## 2. Scelte architetturali
#### VPC:
La conformazione della VPC è facilmente personalizzabile tramite l'utilizzo dei parametri.
Lo stack che deploya la VPC crea sempre delle subnet pubbliche e private.
Il numero di availability zones su cui vengono create le subnet è pilotato dal parametro `az_number`.
In un ambiente di produzione, questo parametro è impostato a `3` per permettere di deployare le varie risorse in alta affidabilità.

Inoltre, per gestire al meglio i costi relativi all'infrastruttura di rete, è possibile decidere tramite il parametro `nats_number` il numero di nat gateway da deployare.
Se il parametro è uguale a `0`, nessun nat gateway e nessuna subnet nattata è creata.
In ambienti di sviluppo è possibile utilizzare un singolo nat gateway per ridurre i costi (un nat gateway grava intorno ai 30 dollari al mese sul billing AWS).
In produzione, invece, è consigliato impostare il parametro `nats_number` a `3` (uno per subnet nattata) per evitare di tagliare completamente l'accesso ad internet dell'applicazione in caso di fail di una AZ.

#### Database:
Per ospitare il database MySql richiesto da Wordpress è stato scelto il servizio gestito di AWS RDS. Più nello specifico è stato utilizzato l'engine Aurora per MySql per la sua migliore integrazione con i servizi AWS e maggiori performance.

A seconda del parametro `aurora.serverless`, è possibile decidere se deployare un cluster serverless o serverful per ogni ambiente.
Per l'ambiente di sviluppo è consigliato l'utilizzo di un cluster serverless per limitare i costi grazie alla funzionalità di spegnimento automatico (dopo x minuti) e scaling fino a 0 capacity units in pochi secondi.
In produzione, invece, è consigliato il deploy di un cluster serverful basato su una istanza sempre attiva ed una di fail over in read replica.

Sconsiglio l'utilizzo di Aurora Serverless v1 in produzione perché fino al rilascio di Aurora Serverless v2, esso [garantisce l'alta disponibilità con ritardi impredittibili](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless.how-it-works.html#aurora-serverless.failover).

Il database è ospitato nelle subnet private per garantire la segregazione da internet. Per garantire però l'accesso al database da parte degli sviluppatori, è stato anche deployato un bastion host a cui accedere tramite SSM o SSH.
#### Compute:

#### CI/CD:

### Possibili ottimizzazioni:
Redis per database e Cloudfront per asset statici di wordpress.


___
####<div style="text-align: right">Christian Calabrese</div>