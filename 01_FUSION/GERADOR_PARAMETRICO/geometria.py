"""Geometria em mm, independente do Fusion. Contornos nominais, sem compensar kerf.
As operacoes de uniao/subtracao de retangulos usam uma grade exata de coordenadas.
"""
import json, math, os

def rect(x,y,w,h): return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]

def ortho(add, sub=()):
    xs=sorted(set(v for r in list(add)+list(sub) for v in (r[0],r[0]+r[2])))
    ys=sorted(set(v for r in list(add)+list(sub) for v in (r[1],r[1]+r[3])))
    def inside(x,y,rs): return any(a-1e-8<x<a+w+1e-8 and b-1e-8<y<b+h+1e-8 for a,b,w,h in rs)
    cells={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1)
           if inside((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2,add)
           and not inside((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2,sub)}
    edges={}
    for i,j in cells:
        corners=[(xs[i],ys[j]),(xs[i+1],ys[j]),(xs[i+1],ys[j+1]),(xs[i],ys[j+1])]
        for k,neigh in enumerate([(i,j-1),(i+1,j),(i,j+1),(i-1,j)]):
            if neigh not in cells: edges[corners[k]]=corners[(k+1)%4]
    loops=[]
    while edges:
        start=next(iter(edges)); cur=start; poly=[]
        while True:
            poly.append(cur); cur=edges.pop(cur)
            if cur==start: break
        # Remove intermediate collinear vertices, including wraparound.
        clean=[]
        for i,p in enumerate(poly):
            a=poly[i-1]; b=poly[(i+1)%len(poly)]
            if abs((p[0]-a[0])*(b[1]-p[1])-(p[1]-a[1])*(b[0]-p[0]))>1e-7: clean.append(p)
        loops.append(clean)
    return loops

def build(p):
    t=p['mdf']; f=p['folga']; W=p['corpo_largura']; D=p['corpo_profundidade']; H=p['corpo_altura']
    B=2*t+p['perna_altura']; parts=[]
    def plate(id,group,loops,origin,u,v,circles=(),note='',cut=True):
        parts.append(dict(id=id,group=group,loops=loops,origin=origin,u=u,v=v,circles=list(circles),note=note,cut=cut))
        return parts[-1]
    # All bases use a right-handed frame: local Z = u cross v.
    def box(prefix,group,w,d,h,x,y,z,face=False,removable=False):
        zs=[(.20*h,.35*h),(.65*h,.80*h)]; xx=[(.22*w,.36*w),(.64*w,.78*w)]
        yy=[(.22*d,.38*d),(.62*d,.78*d)]
        for rear in [False,True]:
            sub=[(edge,a,t+f,b-a) for edge in [0,w-t-f] for a,b in zs]
            sub += [(a,edge,b-a,t+f) for edge in [0,h-t-f] for a,b in xx]
            holes=[]
            if face and not rear: holes=[(w*.32,h*.65,8),(w*.68,h*.65,8)]
            if removable and not rear:
                # Frente MakerLab: LCD 1602 I2C, HC-SR04 e LED de 5 mm.
                # LCD: janela visivel 66 x 16 mm e furos M3 no padrao 75 x 31 mm.
                sub += [(w/2-33,96,66,16)]
                holes += [(w/2+sx*37.5,104+sy*15.5,1.6) for sx in (-1,1) for sy in (-1,1)]
                # HC-SR04: os dois transdutores atravessam a tampa; slots laterais aceitam abracadeira.
                holes += [(w/2-13,58,8.5),(w/2+13,58,8.5),(w/2,27,2.6)]
                sub += [(w/2-27,52,3,12),(w/2+24,52,3,12)]
            if removable and rear: holes=[(a,b,1.7) for a in [t+7,w-t-7] for b in [.42*h,.58*h]]
            if face and not rear: sub += [(w*.38,h*.30,w*.24,3)]
            if removable and rear: sub += [(w/2-12,12,24,18)]
            face_id=prefix+('_TRAS' if rear else ('_FRENTE_MAKER' if removable else '_FRENTE'))
            plate(face_id,'03_Tampa_traseira' if removable and rear else group,
                  ortho([(0,0,w,h)],sub),(x,y+(d if rear else t),z),(1,0,0),(0,0,1),holes,
                  'Nao colar: tampa removivel M3' if removable and rear else '')
        for right in [False,True]:
            add=[(t,0,d-2*t,h)]+[(0,a+f/2,t,b-a-f) for a,b in zs]+[(d-t,a+f/2,t,b-a-f) for a,b in zs]
            sub=[(a,edge,b-a,t+f) for edge in [0,h-t-f] for a,b in yy]
            holes=[]
            if removable:
                # SG90 on the robot's anatomical right (viewer left). Long axis along depth.
                if not right:
                    sw=p['servo_abertura_largura']; sh=p['servo_abertura_altura']; sy=d/2; sz=h-28
                    sub += [(sy-sw/2,sz-sh/2,sw,sh)]
                    holes=[(sy-p['servo_furos_distancia']/2,sz,1.1),(sy+p['servo_furos_distancia']/2,sz,1.1)]
                else: holes=[(d/2,h-28,1.7),(d/2,h-43,1.7)]
            plate(prefix+('_DIR' if not right else '_ESQ'),group,ortho(add,sub),
                  (x+(w-t if right else 0),y,z),(0,1,0),(0,0,1),holes)
        for top in [False,True]:
            add=[(t,t,w-2*t,d-2*t)]
            add += [(a+f/2,edge,b-a-f,t) for edge in [0,d-t] for a,b in xx]
            add += [(edge,a+f/2,t,b-a-f) for edge in [0,w-t] for a,b in yy]
            sub=[]
            if removable and not top:
                # Four leg tongues, 20 mm wide, two per foot.
                sub += [(cx-10-f/2,cy-t/2-f/2,20+f,t+f) for cx in [w*.27,w*.73] for cy in [d*.35,d*.65]]
            if removable and top: sub += [(w/2-12-f/2,d/2-t/2-f/2,24+f,t+f)]
            if face and not top: sub += [(w/2-12-f/2,d/2-t/2-f/2,24+f,t+f)]
            plate(prefix+('_TOPO' if top else '_BASE'),group,ortho(add,sub),
                  (x,y,z+(h-t if top else 0)),(1,0,0),(0,1,0))
    box('C','02_Corpo',W,D,H,-W/2,0,B,removable=True)
    S=p['cabeca']; Z=B+H+p['pescoco_altura']
    box('H','01_Cabeca',S,S,S,-S/2,(D-S)/2,Z,face=True)
    # Neck: one broad upright plate, tabs into head base and body top.
    nh=p['pescoco_altura']; neck=ortho([(-20,0,40,nh),(-12+f/2,-t,24-f,t),(-12+f/2,nh,24-f,t)])
    plate('N_PESCOCO','09_Suportes_internos',neck,(0,D/2+t/2,B+H),(1,0,0),(0,0,1))
    # Feet: two laminated layers; legs have through tongues into the upper foot layer.
    for side,cx in [('D',-.23*W),('E',.23*W)]:
        fw=58; fd=D+25
        for layer in [0,1]:
            sub=[] if layer==0 else [(fw/2-10-f/2,cy+12.5-t/2-f/2,20+f,t+f) for cy in [D*.35,D*.65]]
            plate('P_'+side+str(layer+1),'08_Pes',ortho([(0,0,fw,fd)],sub),(cx-fw/2,-12.5,layer*t),(1,0,0),(0,1,0))
        for j,cy in enumerate([D*.35,D*.65]):
            lh=p['perna_altura']; loops=ortho([(-16,0,32,lh),(-10+f/2,-t,20-f,t),(-10+f/2,lh,20-f,t)])
            plate('L_'+side+str(j+1),'07_Pernas',loops,(cx,cy+t/2,2*t),(1,0,0),(0,0,1))
    # One flat MDF arm per side, local horizontal coordinate = depth, vertical = height.
    L=p['braco_comprimento']; sz=B+H-28; sy=D/2-5.5
    arm=[(-10,12),(10,12),(10,-L+25),(15,-L+25),(15,-L),(5,-L),(5,-L+12),(-5,-L+12),(-5,-L),(-15,-L),(-15,-L+25),(-10,-L+25)]
    plate('A_D_MOVEL','05_Braco_direito',[arm],(-W/2-8,sy,sz),(0,1,0),(0,0,1),[(0,0,3.5),(0,-7,1.0),(0,-14,1.0)],'Usar horn original; confirmar furos no horn real e ajustar antes do corte')
    plate('A_E_FIXO','04_Braco_esquerdo',[arm],(W/2+3,D/2,sz),(0,1,0),(0,0,1),[(0,0,1.7),(0,-15,1.7)])
    # Fixed arm spacers (3 mm thick, two M3 holes).
    plate('A_E_ESP','09_Suportes_internos',[rect(-8,-22,16,30)],(W/2,D/2,sz),(0,1,0),(0,0,1),[(0,0,1.7),(0,-15,1.7)])
    # SG90 load spreader laminated inside right wall. Same aperture and ear holes.
    sw=p['servo_abertura_largura']; sh=p['servo_abertura_altura']; dist=p['servo_furos_distancia']
    plate('S_REFORCO','06_Suporte_servomotor',ortho([(-22,-14,44,28)],[(-sw/2,-sh/2,sw,sh)]),
          (-W/2+t,D/2,sz),(0,1,0),(0,0,1),[(-dist/2,0,1.1),(dist/2,0,1.1)],'Inserir servo pelo interior; orelhas apoiam no reforco; conferir altura do eixo')
    # Rear nut holders: pocket layer open towards cover, cap layer on front.
    for i,cx in enumerate([-W/2+t+7,W/2-t-7]):
        for j,z in enumerate([B+.42*H,B+.58*H]):
            # Hexagon sized for M3 nut, nominal across flats 5.7.
            rr=5.7/math.sqrt(3); hexa=[(7+rr*math.cos(k*math.pi/3),7+rr*math.sin(k*math.pi/3)) for k in range(6)]
            plate('T_PORCA_%s%s'%(i,j),'09_Suportes_internos',[rect(0,0,14,14),hexa],(cx-7,D-t,z-7),(1,0,0),(0,0,1),note='Alojamento M3; colar lateral externa na lateral do corpo')
            plate('T_CAPA_%s%s'%(i,j),'09_Suportes_internos',[rect(0,0,14,14)],(cx-7,D-2*t,z-7),(1,0,0),(0,0,1),[(7,7,1.7)])
    # Electronics tray horizontal: straps avoid depending on board-specific screw positions.
    plate('I_BANDEJA','09_Suportes_internos',ortho([(-50,0,100,70)],[(-44,8,3,22),(41,8,3,22),(-44,40,3,22),(41,40,3,22)]),
          (0,12,B+12),(1,0,0),(0,1,0),note='Arduino Uno em espacadores adesivos/nylon e abracadeiras; nao encostar soldas no MDF')
    for i,cx in enumerate([-48,45]):
        for layer in range(3):
            plate('I_APOIO'+str(i)+str(layer),'09_Suportes_internos',[rect(0,0,3,70)],(cx,12,B+t+layer*t),(1,0,0),(0,1,0),note='Laminar tres unidades para obter 9 mm de apoio')
    # Coupons: slots differ by 0.05 mm; all outlines remain nominal, CAM applies kerf.
    subs=[(8+i*12,8,t+delta,15) for i,delta in enumerate([-.1,-.05,0,.05,.1,.15,.2])]
    plate('TESTE_FEMEA','10_Teste_encaixe',ortho([(0,0,100,32)],subs),(210,0,0),(1,0,0),(0,1,0),note='Da esquerda para direita: t-0.10 a t+0.20 em passos 0.05 mm')
    plate('TESTE_MACHO','10_Teste_encaixe',[rect(0,0,20,25)],(320,0,0),(1,0,0),(0,1,0))
    return parts

def dxf(part,path):
    out=['0','SECTION','2','HEADER','9','$ACADVER','1','AC1015','9','$INSUNITS','70','4','9','$MEASUREMENT','70','1','0','ENDSEC','0','SECTION','2','ENTITIES']
    for loop in part['loops']:
        out += ['0','LWPOLYLINE','100','AcDbEntity','8','CORTE','100','AcDbPolyline','90',str(len(loop)),'70','1']
        for x,y in loop: out += ['10',str(round(x,6)),'20',str(round(y,6))]
    for x,y,r in part['circles']: out += ['0','CIRCLE','100','AcDbEntity','8','CORTE','100','AcDbCircle','10',str(x),'20',str(y),'30','0','40',str(r)]
    out += ['0','ENDSEC','0','EOF']
    with open(path,'w',encoding='ascii') as file: file.write('\n'.join(out)+'\n')

if __name__=='__main__':
    base=os.path.dirname(__file__)
    p=json.load(open(os.path.join(base,'config.json'),encoding='utf-8'))
    parts=build(p); dest=os.path.join(base,'DXF_nominal'); os.makedirs(dest,exist_ok=True)
    for item in parts: dxf(item,os.path.join(dest,item['id']+'.dxf'))
    frente=next(item for item in parts if item['id']=='C_FRENTE_MAKER')
    corte=os.path.abspath(os.path.join(base,'..','..','02_CORTE_LASER'))
    os.makedirs(corte,exist_ok=True)
    dxf(frente,os.path.join(corte,'TAMPA_FRONTAL_MAKER_LCD_HCSR04_LED.dxf'))
    json.dump(parts,open(os.path.join(base,'pecas.json'),'w',encoding='utf-8'),indent=2)
    print(str(len(parts))+' pecas geradas')
