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
1. Installa Python (https://www.python.org/downloads/)
2. Installa node.js (https://nodejs.org/en/download/)
3. Installa la dipendenza npm di CDK con `npm i -g aws-cdk`
4. Installa le dipendenze di sviluppo di Python `pip3 install -r requirements-dev.txt`
5. Crea un Python virtual environment se non esiste `python3 -m venv ./.venv`
6. Attiva il Python virtual environment per evitare di sporcare l'ambiente globale
   1. Windows `.\.venv\bin\activate`
   2. Unix `source .venv/bin/activate`
7. Installa le dipendenze Python `pip3 install -r requirements.txt`
8. Imposta la variabile d'ambiente ENVIRONMENT a dev o prod in base all'ambiente da deployare
9. Deploya l'infrastruttura tramite `cdk deploy`

## 2. Scelte architetturali
### VPC:
La conformazione della VPC è facilmente personalizzabile tramite l'utilizzo dei parametri.
Lo stack che deploya la VPC crea sempre delle subnet pubbliche e private.
Il numero di availability zones su cui vengono create le subnet è pilotato dal parametro `az_number`.
In un ambiente di produzione, questo parametro è impostato a `3` per permettere di deployare le varie risorse in alta affidabilità.

Inoltre, per gestire al meglio i costi relativi all'infrastruttura di rete, è possibile decidere tramite il parametro `nats_number` il numero di nat gateway da deployare.
In ambienti di sviluppo è possibile utilizzare un singolo nat gateway per ridurre i costi (un nat gateway grava intorno ai 30 dollari al mese sul billing AWS).
In produzione, invece, è consigliato impostare il parametro `nats_number` a `3` (uno per subnet nattata) per evitare di tagliare completamente l'accesso ad internet dell'applicazione in caso di fail di una AZ.

### Database:
Per ospitare il database MySql richiesto da Wordpress è stato scelto il servizio gestito di AWS RDS. Più nello specifico è stato utilizzato l'engine Aurora per MySql per la sua migliore integrazione con i servizi AWS e maggiori performance.

A seconda del parametro `aurora.serverless`, è possibile decidere se deployare un cluster serverless o serverful per ogni ambiente.
Per l'ambiente di sviluppo è consigliato l'utilizzo di un cluster serverless per limitare i costi grazie alla funzionalità di spegnimento automatico (dopo x minuti) e scaling fino a 0 capacity units in pochi secondi.
In produzione, invece, è consigliato il deploy di un cluster serverful basato su una istanza sempre attiva ed una di fail over in read replica.
Per ovviare alla creazione del nat gateway e delle subnet annesse, è possibile creare dei VPC endpoint e/o Gateway Endpoints per permettere il raggiungimento dei servizi AWS in maniera sicura.
Sconsiglio l'utilizzo di Aurora Serverless v1 in produzione perché fino al rilascio di Aurora Serverless v2, esso [garantisce l'alta disponibilità con ritardi impredittibili](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless.how-it-works.html#aurora-serverless.failover).

Il database è ospitato nelle subnet private per garantire la segregazione da internet. Per garantire però l'accesso al database da parte degli sviluppatori, è stato anche deployato un bastion host a cui accedere tramite SSM o SSH.
### Compute:
Come risorsa di computing su cui ospitare l'application server e Wordpress, è stato scelto di utilizzare ECS in modalità Fargate.
I container Fargate saranno spawnati su subnet nattate per permettere l'accesso ai diversi servizi AWS come ECR ed alla rete internet.

Inoltre, è stata implementata una regola di autoscaling che effettua scale-out quando il container raggiunge il 75% di cpu utilization con un cooldown in scale-in e scale-out di 30 secondi.
Per bilanciare il carico verso i container spawnati nelle diverse AZ, è stato creato un Application Load Balancer.
Per contenere i costi di fargate, è stata aggiunta la possibilità di creare una parte dei container in modalità Spot. Tramite i parametri `fargate.spot_weight` e `fargate.normal_weight` si può decidere la strategia utilizzata dall'autoscaling per scegliere il tipo di container da spawnare.

Avendo la necessità di comunicare con il database MySql, i container sono inclusi in un security group che permette la rotta verso il cluster sulla porta default di MySql (3306).

Inoltre, è stato creato un bucket S3 che contiene gli asset statici di Wordpress. Per permettere la comunicazione del CMS con il Bucket, è stato installato un plug-in tramite la Wordpress CLI (nel Dockerfile) e configurato nel wp-config.php.

### CI/CD:
Per soddisfare i requisiti di CI/CD, è stato scelto di creare una semplice pipeline tramite il servizio CodePipeline.
Essa è composta da due fasi:
   1. Source: il codice di questo repository è prelevato automaticamente da GitHub ad ogni commit. Per permettere l'integrazione tra CodePipeline e GitHub è necessario utilizzare un token oAuth salvato in un secret su secrets manager prima di creare la pipeline.
   2. Build and deploy: questa fase è gestita tramite container CodeBuild su base Amazon Linux 2. Al suo interno sono installate le runtime di NodeJs e Python. Il primo è necessario per l'utilizzo di CDK ed il secondo per l'interpretazione dello IaC di questo repository. 
   
Il vantaggio di utilizzare CDK è infatti la possibilità di mantenere una forte sinergia tra l'infrastruttura ed il codice.
Nel caso di questo progetto, ad esempio, il Dockerfile di Wordpress per la creazione dei container e la definizione della loro infrastruttura sono inclusi nello stesso repository,
rendendo impossibile il deploy disgiunto delle due parti.
Questa caratteristica viene sfruttata maggiormente quando sono presenti delle funzioni Lambda. Infatti, è possibile mantenere il codice di infrastruttura CDK e Back-End nella stessa code base ed utilizzando lo stesso linguaggio di programmazione.

### Possibili ottimizzazioni:
Esistono molti spiragli di ottimizzazione e miglioramento del progetto.
In questo paragrafo sono elencati quelli più importanti che ho identificato:
   1. Testing: il framework utilizzato (CDK) permette il testing dello IaC per assicurarsi che le risorse create siano corrette in ogni loro parte. Per evitare deploy errati, è possibile aggiungere una fase di test nella pipeline di CI/CD per bloccare il processo di deploy in caso di fallimento.
   2. Per diminuire il carico sul database e velocizzare le query di Wordpress è possibile istanziare un sistema di caching in-memory come Redis o memcached tramite il servizio gestito di AWS ElastiCache.
   3. Utilizzando le caratteristiche di CloudFront è possibile diminuire il numero di richieste di GET agli oggetti contenuti nel bucket S3 contenente gli asset statici di Wordpress. In questo modo si riducono i costi di S3, velocizzando anche il serving delle pagine web.
   4. In questo momento, lo IaC implementato permette l'accesso a Wordpress tramite protocollo HTTP. È molto importante, però, dismetterne l'utilizzo in favore di HTTPS. Per fare ciò è possibile generare un certificato SSL tramite AWS Certificate Manager. Grazie alla feature di TLS session termination dei Load Balancer, è poi possibile abilitare l'HTTPS facilmente con il certificato creato.

___
<h4 style="text-align: right">Christian Calabrese</h4>