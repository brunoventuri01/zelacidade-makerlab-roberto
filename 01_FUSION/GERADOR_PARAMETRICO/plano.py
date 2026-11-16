"""Prancha virtual para inspecao, sem presumir tamanho de maquina."""
import adsk.core,adsk.fusion,os,json,importlib.util,traceback
BASE=os.path.dirname(os.path.realpath(__file__))
def run(context):
    app=adsk.core.Application.get()
    try:
        spec=importlib.util.spec_from_file_location('geometria_plana',os.path.join(BASE,'geometria.py'))
        geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
        parts=json.load(open(os.path.join(BASE,'pecas.json')))
        cfg=json.load(open(os.path.join(BASE,'config.json')))
        for part in parts:
            pts=[pt for loop in part['loops'] for pt in loop]
            part['bounds']=[min(a for a,b in pts),min(b for a,b in pts),max(a for a,b in pts),max(b for a,b in pts)]
        parts.sort(key=lambda part: (-(part['bounds'][3]-part['bounds'][1]),part['id']))
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name='CP5 - Todas as pecas - Vista de corte'
        design=adsk.fusion.Design.cast(app.activeProduct)
        design.designType=adsk.fusion.DesignTypes.ParametricDesignType
        design.unitsManager.distanceDisplayUnits=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root=design.rootComponent
        root.attributes.add('RoboMDF','nota','Prancha virtual para visualizacao. Nao representa mesa ou nesting definitivo. DXF nominal sem kerf.')
        x=y=rowh=maxx=0; gap=10; display_width=900
        combined={'loops':[],'circles':[]}; locations=[]
        def point(x,y,z=0):return adsk.core.Point3D.create(x/10,y/10,z/10)
        for part in parts:
            x0,y0,x1,y1=part['bounds']; w=x1-x0;h=y1-y0
            if x and x+w>display_width: x=0;y+=rowh+gap;rowh=0
            dx=x-x0;dy=y-y0
            trans=adsk.core.Matrix3D.create();trans.translation=adsk.core.Vector3D.create(dx/10,dy/10,0)
            occ=root.occurrences.addNewComponent(trans);comp=occ.component;comp.name=part['id']
            sk=comp.sketches.add(comp.xYConstructionPlane);sk.name=part['id']+'_CORTE';sk.isComputeDeferred=True
            for loop in part['loops']:
                for i,a in enumerate(loop):
                    sk.sketchCurves.sketchLines.addByTwoPoints(point(*a),point(*loop[(i+1)%len(loop)]))
                combined['loops'].append([(a+dx,b+dy) for a,b in loop])
            for a,b,r in part['circles']:
                sk.sketchCurves.sketchCircles.addByCenterRadius(point(a,b),r/10)
                combined['circles'].append((a+dx,b+dy,r))
            sk.isComputeDeferred=False
            profile=max([sk.profiles.item(i) for i in range(sk.profiles.count)],key=lambda q:q.areaProperties().area)
            ext=comp.features.extrudeFeatures.addSimple(profile,adsk.core.ValueInput.createByReal(cfg['mdf']/10),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ext.name=part['id'];sk.isVisible=False
            locations.append(dict(id=part['id'],x_mm=x,y_mm=y,largura_mm=w,altura_mm=h))
            x+=w+gap;rowh=max(rowh,h);maxx=max(maxx,x-gap);adsk.doEvents()
        totalh=y+rowh
        geo.dxf(combined,os.path.join(BASE,'Todas_as_pecas_VISUALIZACAO.dxf'))
        camera=app.activeViewport.camera
        camera.cameraType=adsk.core.CameraTypes.OrthographicCameraType
        camera.eye=point(maxx/2,totalh/2,1000);camera.target=point(maxx/2,totalh/2,0)
        camera.upVector=adsk.core.Vector3D.create(0,1,0);camera.isFitView=True
        app.activeViewport.camera=camera;app.activeViewport.fit();app.activeViewport.refresh()
        manager=design.exportManager
        manager.execute(manager.createFusionArchiveExportOptions(os.path.join(BASE,'CP5_Vista_de_Corte.f3d')))
        app.activeViewport.saveAsImageFile(os.path.join(BASE,'Vista_de_corte.png'),1800,1100)
        json.dump(dict(pecas=len(parts),largura_virtual_mm=maxx,altura_virtual_mm=totalh,posicoes=locations),open(os.path.join(BASE,'plano_resultado.json'),'w'),indent=2)
    except:
        err=traceback.format_exc();open(os.path.join(BASE,'erro_plano.txt'),'w').write(err);app.userInterface.messageBox(err)
