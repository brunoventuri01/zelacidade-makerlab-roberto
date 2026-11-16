"""Executar no Autodesk Fusion. Gera uma NOVA revisao sem apagar documentos.
Para redimensionar: altere parametros de usuario e execute novamente este script.
Os contornos sao regenerados; extrusoes usam a expressao mdf.
"""
import adsk.core, adsk.fusion, traceback, os, json, math, importlib.util

BASE=os.path.dirname(os.path.realpath(__file__))

def run(context):
    app=adsk.core.Application.get(); ui=app.userInterface
    try:
        # One-shot request to open a flat inspection document, preserving the assembly.
        flag=os.path.join(BASE,'abrir_vista_corte.flag')
        if os.path.isfile(flag):
            os.remove(flag)
            flat_spec=importlib.util.spec_from_file_location('robo_plano',os.path.join(BASE,'plano.py'))
            flat=importlib.util.module_from_spec(flat_spec);flat_spec.loader.exec_module(flat)
            flat.run(context)
            return
        spec=importlib.util.spec_from_file_location('robo_geometria',os.path.join(BASE,'geometria.py'))
        geo=importlib.util.module_from_spec(spec); spec.loader.exec_module(geo)
        p=json.load(open(os.path.join(BASE,'config.json'),encoding='utf-8'))
        source=adsk.fusion.Design.cast(app.activeProduct)
        if source and source.rootComponent.attributes.itemByName('RoboMDF','gerador'):
            for name in p:
                par=source.userParameters.itemByName(name)
                if par: p[name]=par.value*10 if name!='angulo_braco_graus' else par.value*180/math.pi
        parts=geo.build(p)
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name='CP5 - Robo Inteligente MDF'
        design=adsk.fusion.Design.cast(app.activeProduct)
        design.designType=adsk.fusion.DesignTypes.ParametricDesignType
        design.unitsManager.distanceDisplayUnits=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root=design.rootComponent
        root.attributes.add('RoboMDF','gerador','1')
        for key,val in p.items():
            unit='deg' if key=='angulo_braco_graus' else 'mm'
            design.userParameters.add(key,adsk.core.ValueInput.createByString(str(val)+' '+unit),unit,
                'Alterar e executar RoboMDF novamente para regenerar contornos e montagem')
        groups={}; rows=[]; dest=os.path.join(BASE,'DXF_nominal'); os.makedirs(dest,exist_ok=True)
        def point(x,y,z=0): return adsk.core.Point3D.create(x/10,y/10,z/10)
        def vec(a): return adsk.core.Vector3D.create(*a)
        for index,part in enumerate(parts):
            group=part['group']
            if group not in groups:
                occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); occ.component.name=group; groups[group]=occ.component
            tr=adsk.core.Matrix3D.create(); u=list(part['u']); v=list(part['v'])
            if part['id']=='A_D_MOVEL':
                a=math.radians(p['angulo_braco_graus']); u=[0,math.cos(a),math.sin(a)]; v=[0,-math.sin(a),math.cos(a)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            tr.setWithCoordinateSystem(point(*part['origin']),vec(u),vec(v),vec(n))
            occ=groups[group].occurrences.addNewComponent(tr); comp=occ.component; comp.name=part['id']
            comp.attributes.add('RoboMDF','nota',part['note'])
            sk=comp.sketches.add(comp.xYConstructionPlane); sk.name=part['id']+'_CORTE_1a1'
            sk.isComputeDeferred=True
            for poly in part['loops']:
                for i,a in enumerate(poly):
                    b=poly[(i+1)%len(poly)]
                    line=sk.sketchCurves.sketchLines.addByTwoPoints(point(*a),point(*b))
                    line.isFixed=True
            for x,y,r in part['circles']:
                c=sk.sketchCurves.sketchCircles.addByCenterRadius(point(x,y),r/10); c.isFixed=True
            sk.isComputeDeferred=False
            if sk.profiles.count==0: raise RuntimeError('Sem perfil fechado: '+part['id'])
            profile=max([sk.profiles.item(i) for i in range(sk.profiles.count)],key=lambda pr:pr.areaProperties().area)
            ext=comp.features.extrudeFeatures.addSimple(profile,adsk.core.ValueInput.createByString('mdf'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext.name=part['id']+'_MDF'; body=ext.bodies.item(0); body.name=part['id']; sk.isVisible=False
            geo.dxf(part,os.path.join(dest,part['id']+'.dxf'))
            rows.append(dict(id=part['id'],volume_mm3=body.volume*1000,faces=body.faces.count))
            adsk.doEvents()
        # Hide calibration coupons from the assembled robot.
        for occ in root.occurrences:
            if occ.component.name=='10_Teste_encaixe': occ.isLightBulbOn=False
        root.attributes.add('RoboMDF','observacao','Protótipo para revisão. Conferir servo/horn, corte de teste e montagem real. Contornos regenerados por script.')
        design.computeAll()
        manager=design.exportManager
        archive=os.path.join(BASE,'CP5_Robo_Inteligente_MDF.f3d')
        ok=manager.execute(manager.createFusionArchiveExportOptions(archive))
        camera=app.activeViewport.camera
        camera.eye=point(420,-650,410); camera.target=point(0,45,150); camera.upVector=vec([0,0,1]); camera.isFitView=True
        app.activeViewport.camera=camera; app.activeViewport.fit(); app.activeViewport.refresh()
        try: app.activeViewport.saveAsImageFile(os.path.join(BASE,'montagem_Fusion.png'),1600,1200)
        except: pass
        json.dump(dict(exportado=ok,pecas=rows,parametros=p),open(os.path.join(BASE,'resultado_fusion.json'),'w',encoding='utf-8'),indent=2)
        ui.messageBox('Modelo criado: '+str(len(parts))+' pecas.\nArquivo F3D e DXFs salvos em:\n'+BASE+'\n\nRevisar medidas do SG90/horn e fazer teste de encaixe antes de cortar.\nPara alterar dimensoes: parametros de usuario + executar script novamente.','Robo MDF - revisao 1')
    except:
        error=traceback.format_exc()
        open(os.path.join(BASE,'erro_fusion.txt'),'w',encoding='utf-8').write(error)
        ui.messageBox(error,'Erro Robo MDF')
