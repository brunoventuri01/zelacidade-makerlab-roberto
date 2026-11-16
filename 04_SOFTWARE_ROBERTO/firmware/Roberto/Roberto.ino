// Roberto GS 2026: Uno R3/Nano classico ATmega328P, logica de 5 V.
// SG90: D9. LED: D6 via INPUT_PULLUP. HC-SR04: D2/D3. LCD I2C: A4/A5.
// O servo usa 4 pilhas AA; o negativo das pilhas deve compartilhar o GND do Arduino.
#include <Servo.h>
#include <Wire.h>

Servo braco;
const byte PIN_SERVO=9, PIN_LED=6, PIN_TRIG=2, PIN_ECHO=3;
// Sentido ajustado conforme a montagem fisica do Roberto.
const int ANGULO_BAIXO=55, ANGULO_ALTO=135;
const float LIMITE_OBSTACULO=30.0, LIMITE_ATENCAO=70.0;
int atual=ANGULO_BAIXO;
String linha;
byte lcdAddr=0;
unsigned long proximaLeitura=0;
byte estadoAnterior=255;

// Driver minimo para o adaptador I2C PCF8574 do LCD 1602 (mapeamento mais comum).
void lcdExpander(byte valor){
  if(!lcdAddr)return;
  Wire.beginTransmission(lcdAddr);Wire.write(valor|0x08);Wire.endTransmission();
}
void lcdPulso(byte valor){lcdExpander(valor|0x04);delayMicroseconds(1);lcdExpander(valor&~0x04);delayMicroseconds(50);}
void lcdNibble(byte valor,byte modo){byte dado=(valor&0xF0)|modo;lcdExpander(dado);lcdPulso(dado);}
void lcdEnviar(byte valor,byte modo){lcdNibble(valor,modo);lcdNibble(valor<<4,modo);}
void lcdComando(byte valor){lcdEnviar(valor,0);}
void lcdLinha(byte linha,const char *texto){
  if(!lcdAddr)return;
  lcdComando(linha?0xC0:0x80);
  bool terminou=false;
  for(byte i=0;i<16;i++){char c=terminou?' ':texto[i];if(!c){terminou=true;c=' ';}lcdEnviar(c,0x01);}
}
void iniciarLcd(){
  Wire.begin();
  const byte candidatos[]={0x27,0x3F};
  for(byte i=0;i<2;i++){Wire.beginTransmission(candidatos[i]);if(Wire.endTransmission()==0){lcdAddr=candidatos[i];break;}}
  if(!lcdAddr)return;
  delay(50);lcdNibble(0x30,0);delay(5);lcdNibble(0x30,0);delayMicroseconds(150);lcdNibble(0x30,0);lcdNibble(0x20,0);
  lcdComando(0x28);lcdComando(0x0C);lcdComando(0x06);lcdComando(0x01);delay(2);
  lcdLinha(0,"ROBERTO ATIVO");lcdLinha(1,"INICIANDO...");
}

String campo(const String &s,const String &nome){
  int i=s.indexOf("\""+nome+"\"");if(i<0)return "";
  i=s.indexOf(':',i);i=s.indexOf('"',i);if(i<0)return "";
  int fim=s.indexOf('"',i+1);return fim<0?"":s.substring(i+1,fim);
}

// Envia o angulo final de uma vez: o SG90 se move na velocidade maxima dele.
void mover(int destino){atual=destino;braco.write(atual);delay(150);}
// O LED utilizado possui resistor em serie integrado.
void luz(bool acesa){pinMode(PIN_LED,OUTPUT);digitalWrite(PIN_LED,acesa?HIGH:LOW);}

float medirDistanciaCm(){
  digitalWrite(PIN_TRIG,LOW);delayMicroseconds(3);digitalWrite(PIN_TRIG,HIGH);delayMicroseconds(10);digitalWrite(PIN_TRIG,LOW);
  unsigned long duracao=pulseIn(PIN_ECHO,HIGH,25000UL);
  if(!duracao)return -1.0;
  float cm=duracao*0.0343/2.0;
  return (cm>=2.0&&cm<=400.0)?cm:-1.0;
}

void mostrarDistancia(float cm){
  char topo[17],baixo[17];
  if(cm<0){strcpy(topo,"SENSOR SEM SINAL");strcpy(baixo,"VERIFIQUE FIOS");}
  else{
    if(cm<=LIMITE_OBSTACULO)strcpy(topo,"!! OBSTACULO !!");
    else if(cm<=LIMITE_ATENCAO)strcpy(topo,"ATENCAO");
    else strcpy(topo,"CAMINHO LIVRE");
    snprintf(baixo,sizeof(baixo),"DIST: %3d CM",(int)(cm+0.5));
  }
  lcdLinha(0,topo);lcdLinha(1,baixo);
}

// Decisao autonoma contextual: 0 livre, 1 atencao, 2 obstaculo.
// Atua somente quando o estado muda, evitando repeticao e tremedeira.
void aplicarDecisao(float cm){
  if(cm<0)return;
  byte estado=cm<=LIMITE_OBSTACULO?2:(cm<=LIMITE_ATENCAO?1:0);
  if(estado==estadoAnterior)return;
  estadoAnterior=estado;
  if(estado==2){luz(true);mover(ANGULO_ALTO);}
  else if(estado==1){luz(true);mover(ANGULO_BAIXO);}
  else{luz(false);mover(ANGULO_BAIXO);}
}

void inicioResposta(const String &id){Serial.print("{\"id\":\"");Serial.print(id);Serial.print("\"");}

void executar(String s){
  String id=campo(s,"id"),acao=campo(s,"action");
  if(id.length()==0||id.length()>32)return;
  for(unsigned int i=0;i<id.length();i++)if(!isAlphaNumeric(id[i]))return;
  if(acao=="SENSOR_READ"){
    float cm=medirDistanciaCm();mostrarDistancia(cm);inicioResposta(id);
    if(cm<0)Serial.println(",\"ok\":false,\"error\":\"sensor_timeout\"}");
    else{Serial.print(",\"ok\":true,\"distance_cm\":");Serial.print(cm,1);Serial.println("}");}
    return;
  }
  bool ok=true;
  if(acao=="ARM_UP")mover(ANGULO_ALTO);
  else if(acao=="ARM_DOWN")mover(ANGULO_BAIXO);
  else if(acao=="LED_ON")luz(true);
  else if(acao=="LED_OFF")luz(false);
  else if(acao=="WAVE"){int anterior=atual;for(byte i=0;i<2;i++){mover(ANGULO_ALTO);mover(ANGULO_ALTO+20);}mover(anterior);}
  else ok=false;
  inicioResposta(id);Serial.print(",\"ok\":");Serial.print(ok?"true":"false");Serial.println("}");
}

void setup(){
  luz(false);
  pinMode(PIN_TRIG,OUTPUT);digitalWrite(PIN_TRIG,LOW);pinMode(PIN_ECHO,INPUT);
  braco.attach(PIN_SERVO);braco.write(atual);
  Serial.begin(115200);linha.reserve(160);iniciarLcd();
}

void loop(){
  while(Serial.available()){
    char c=Serial.read();
    if(c=='\n'){executar(linha);linha="";}
    else if(c!='\r'){if(linha.length()<160)linha+=c;else linha="";}
  }
  if((long)(millis()-proximaLeitura)>=0){
    float cm=medirDistanciaCm();mostrarDistancia(cm);aplicarDecisao(cm);proximaLeitura=millis()+500;
  }
}
