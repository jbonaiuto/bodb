from django.db.models import Q
import reportlab
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PyRTF import *
import PyRTF
import reportlab
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import *
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from bodb.models import BOP, compareDocuments, compareRelatedModels, compareRelatedBops, compareBuildSEDs, compareRelatedBrainRegions, Literature, BuildSED, RelatedBOP, RelatedModel, RelatedBrainRegion, DocumentFigure, Variable, Model, Module, TestSED, Prediction, compareVariables, compareModules, SED, SSR, BrainImagingSED, SEDCoord, compareTestSEDs
from uscbp.image_utils import get_thumbnail

thin_edge  = BorderPS( width=10, style=BorderPS.SINGLE )
thin_frame  = FramePS( thin_edge,  thin_edge,  thin_edge,  thin_edge )
styles = getSampleStyleSheet()

def get_sed_report_context(request, sed):
    # load related entries
    figures = list(DocumentFigure.objects.filter(document=sed).order_by('order'))
    related_bops = list(RelatedBOP.get_related_bops(sed, request.user))
    related_models = RelatedModel.get_sed_related_models(sed, request.user)
    related_brain_regions = list(RelatedBrainRegion.objects.filter(document=sed))
    references = list(sed.literature.all())
    related_bops.sort(compareRelatedBops)
    related_models.sort(compareRelatedModels)
    related_brain_regions.sort(compareRelatedBrainRegions)
    references.sort(key=Literature.author_names)
    context = {
        'sed': sed,
        'figures': figures,
        'related_bops': related_bops,
        'related_models': related_models,
        'related_brain_regions': related_brain_regions,
        'references': references
    }
    return context

class BOPReportView(View):
    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('pk', None)
        format = self.kwargs.get('format', None)

        ############### Obtaining BOP information (James) #########################
        bop=get_object_or_404(BOP, id=id)

        # load related entries
        figures = DocumentFigure.objects.filter(document=bop).order_by('order')
        child_bops = list(BOP.get_child_bops(bop,request.user))
        building_seds = list(BuildSED.get_building_seds(bop,request.user))
        related_bops = list(RelatedBOP.get_related_bops(bop, request.user))
        related_models = list(RelatedModel.get_related_models(bop, request.user))
        related_brain_regions = list(RelatedBrainRegion.objects.filter(document=bop))
        references = list(bop.literature.all())

        child_bops.sort(compareDocuments)
        related_models.sort(compareRelatedModels)
        related_bops.sort(compareRelatedBops)
        building_seds.sort(compareBuildSEDs)
        related_brain_regions.sort(compareRelatedBrainRegions)
        references.sort(key=Literature.author_names)

        context={
            'bop': bop,
            'figures': figures,
            'child_bops': child_bops,
            'building_seds': building_seds,
            'related_bops': related_bops,
            'related_models': related_models,
            'related_brain_regions': related_brain_regions,
            'references':references,
        }

        display_settings={
            'figuredisp': int(request.POST['figureDisplay']),
            'narrativedisp': int(request.POST['narrativeDisplay']),
            'childbopdisp': int(request.POST['childBopDisplay']),
            'seddisp': int(request.POST['summaryDisplay']),
            'relatedmodeldisp': int(request.POST['relatedModelDisplay']),
            'relatedbopdisp': int(request.POST['relatedBopDisplay']),
            'relatedregiondisp': int(request.POST['relatedBrainRegionDisplay']),
            'referencedisp': int(request.POST['referenceDisplay'])
        }

        response = HttpResponse(mimetype='application/%s' % format)
        response['Content-Disposition'] = 'attachment; filename=BOP_Report.%s' % format


        if format=='rtf':
            doc=bop_report_rtf(context, display_settings)
        elif format=='pdf':
            elements=bop_report_pdf(context, display_settings)

        if request.POST['includeSEDs']=='true':
            display_settings={
                'figuredisp': 1,
                'narrativedisp': 1,
                'relatedbopdisp': 1,
                'relatedmodeldisp': 1,
                'relatedregiondisp': 1,
                'referencedisp': 1

            }
            for buildsed in context['building_seds'] :
                bsed_context = get_sed_report_context(request, buildsed.sed)
                if format=='rtf':
                    doc=sed_report_rtf(bsed_context, display_settings, doc=doc)
                elif format=='pdf':
                    elements=sed_report_pdf(bsed_context, display_settings, elements=elements)

        if format=='rtf':
            DR = Renderer()
            DR.Write(doc,response)
        elif format=='pdf':
            ##############################################################################
            # Create the PDF object, using the response object as its "file."
            doc = SimpleDocTemplate(response)
            doc.build(elements)
        return response


# Report generator for Model page
class ModelReportView(View):

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('pk', None)
        format = self.kwargs.get('format', None)

        ############### Obtaining model information (James) #########################
        # load model, submodules and variables
        model=get_object_or_404(Model, id=id)
        figures = DocumentFigure.objects.filter(document=model).order_by('order')
        input_ports = list(Variable.objects.filter(var_type='Input',module=model))
        output_ports = list(Variable.objects.filter(var_type='output', module=model))
        states = list(Variable.objects.filter(var_type='state', module=model))
        modules = list(Module.objects.filter(parent=model))

        # load related entries
        related_models = list(RelatedModel.get_related_models(model, request.user))
        related_bops = list(RelatedBOP.get_related_bops(model, request.user))
        related_brain_regions = list(RelatedBrainRegion.objects.filter(document=model))
        building_seds = list(BuildSED.get_building_seds(model,request.user))
        testing_seds = list(TestSED.get_testing_seds(model,request.user))
        predictions = list(Prediction.get_predictions(model,request.user))
        references = list(model.literature.all())

        input_ports.sort(compareVariables)
        output_ports.sort(compareVariables)
        states.sort(compareVariables)
        modules.sort(compareModules)
        building_seds.sort(compareBuildSEDs)
        testing_seds.sort(compareTestSEDs)
        predictions.sort(compareDocuments)
        related_models.sort(compareRelatedModels)
        related_bops.sort(compareRelatedBops)
        related_brain_regions.sort(compareRelatedBrainRegions)
        references.sort(key=Literature.author_names)

        context={
            'model': model,
            'figures': figures,
            'input_ports': input_ports,
            'output_ports': output_ports,
            'states': states,
            'modules': modules,
            'related_models': related_models,
            'related_bops': related_bops,
            'related_brain_regions': related_brain_regions,
            'building_seds': building_seds,
            'testing_seds': testing_seds,
            'predictions': predictions,
            'references': references
        }

        display_settings={
            'figuredisp': int(request.POST['figureDisplay']),
            'narrativedisp': int(request.POST['narrativeDisplay']),
            'seddisp': int(request.POST['summaryDisplay']),
            'urldisp': int(request.POST['urlDisplay']),
            'relatedmodeldisp': int(request.POST['relatedModelDisplay']),
            'relatedbopdisp': int(request.POST['relatedBopDisplay']),
            'relatedregiondisp': int(request.POST['relatedBrainRegionDisplay']),
            'referencedisp': int(request.POST['referenceDisplay'])
        }

        response = HttpResponse(mimetype='application/%s' % format)
        response['Content-Disposition'] = 'attachment; filename=Model_Report.%s' % format

        if format=='rtf':
            doc=model_report_rtf(context, display_settings)
        elif format=='pdf':
            elements=model_report_pdf(context, display_settings)

        if request.POST['includeSEDs']=='true':
            display_settings={
                'figuredisp': 1,
                'narrativedisp': 1,
                'relatedbopdisp': 1,
                'relatedmodeldisp': 1,
                'relatedregiondisp': 1,
                'referencedisp': 1

            }
            for buildsed in context['building_seds'] :
                bsed_context = get_sed_report_context(request, buildsed.sed)
                if format=='rtf':
                    doc=sed_report_rtf(bsed_context, display_settings, doc=doc)
                elif format=='pdf':
                    elements=sed_report_pdf(bsed_context, display_settings, elements=elements)

            for testsed in context['testing_seds']:
                tsed_context = get_sed_report_context(request, testsed.sed)
                if format=='rtf':
                    doc=sed_report_rtf(tsed_context, display_settings, doc=doc)
                elif format=='pdf':
                    elements=sed_report_pdf(tsed_context, display_settings, elements=elements)

        if format=='rtf':
            DR = Renderer()
            DR.Write(doc,response)
        elif format=='pdf':
            doc = SimpleDocTemplate(response)
            doc.build(elements)

        return response


# Report generator for SED page
class SEDReportView(View):
    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('pk', None)
        format = self.kwargs.get('format', None)

        sed=get_object_or_404(SED, id=id)
        context = get_sed_report_context(request, sed)

        display_settings={
            'figuredisp': int(request.POST['figureDisplay']),
            'narrativedisp': int(request.POST['narrativeDisplay']),
            'relatedbopdisp': int(request.POST['relatedBopDisplay']),
            'relatedmodeldisp': int(request.POST['relatedModelDisplay']),
            'relatedregiondisp': int(request.POST['relatedBrainRegionDisplay']),
            'referencedisp': int(request.POST['referenceDisplay'])

        }

        response = HttpResponse(mimetype='application/%s' % format)
        response['Content-Disposition'] = 'attachment; filename=SED_Report.%s' % format

        if format=='rtf':
            doc=sed_report_rtf(context, display_settings)
            DR = Renderer()
            DR.Write(doc,response)
        elif format=='pdf':
            doc = SimpleDocTemplate(response)
            elements=sed_report_pdf(context, display_settings)
            doc.build(elements)
        elif format=='json':
            response=report_json(context, display_settings)
        return response
        

import json
from bodb.serializers.sed import SEDSerializer
from rest_framework.renderers import UnicodeJSONRenderer
#from rest_framework.response import Response

def report_json(context, display_settings):
    response = HttpResponse(mimetype='application/json')
    response['Content-Disposition'] = 'attachment; filename=SED_Report.json'
    
    serializer = SEDSerializer(context['sed'])
    data = UnicodeJSONRenderer().render(serializer.data)
    json.dump(data, response)

    return response


# Report generator for SSR page
class SSRReportView(View):
    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('pk', None)
        format = self.kwargs.get('format', None)

        ssr=get_object_or_404(SSR, id=id)
        # load related entries
        model=Model.objects.filter(Q(testsed__testsedssr__ssr=ssr) | Q(prediction__predictionssr__ssr=ssr))[0]
        figures=list(DocumentFigure.objects.filter(document=ssr).order_by('order'))

        context={
            'ssr':ssr,
            'model':model,
            'figures':figures
        }

        display_settings={
            'figuredisp': int(request.POST['figureDisplay']),
            'narrativedisp': int(request.POST['narrativeDisplay']),
        }
        response = HttpResponse(mimetype='application/%s' % format)
        response['Content-Disposition'] = 'attachment; filename=SSR_Report.%s' % format

        if format=='rtf':
            doc=ssr_report_rtf(context, display_settings)
            DR = Renderer()
            DR.Write(doc,response)
        elif format=='pdf':
            doc = SimpleDocTemplate(response)
            elements=ssr_report_pdf(context, display_settings)
            doc.build(elements)
        return response


def ssr_report_rtf(context, display_settings, doc=None):
    # Create the document
    if doc is None:
        doc = PyRTF.Elements.Document()
    ss = doc.StyleSheet
    NormalText = TextStyle( TextPropertySet( ss.Fonts.Arial, 22 ) )
    NormalText.TextPropertySet.SetSize(22).SetBold(True).SetUnderline(False).SetItalic(False)
    ps = ParagraphStyle( 'Heading 5', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(24).SetBold(True).SetUnderline(True).SetItalic(False)
    ps = ParagraphStyle( 'Heading 4', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(26).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 3', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(28).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 2', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(32).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 1', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    section = Section()
    doc.Sections.append( section )

    #print ssr title
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading1)
    p.append('SSR: %s' % unicode(context['ssr'].title).encode('latin1','ignore'))
    section.append(p)

    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading1)
    p.append('Model: %s' % unicode(context['model']).encode('latin1','ignore'))
    section.append(p)

    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 6 )
    table.SetGapBetweenCells(0)

    #print ssr description
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Brief Description *'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(context['ssr'].brief_description).encode('latin1','ignore')), thin_frame)
    c2.SetSpan(2)
    table.AddRow(c1, c2)

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['ssr'].narrative and len(context['ssr'].narrative):
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Narrative *'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(context['ssr'].narrative).encode('latin1','ignore')), thin_frame)
        c2.SetSpan(2)
        table.AddRow(c1, c2)

    # Tags
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Tags'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(', '.join(context['ssr'].tags.names())).encode('latin1','ignore')), thin_frame)
    c2.SetSpan(2)
    table.AddRow(c1, c2)

    section.append(table)

    #print figures
    if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
        section=figure_section_rtf(section, ss, context['figures'])

    # RelatedModel
#    if relatedmodeldisp and related_models and len(related_models) :
#        section=related_model_section_rtf(section, ss, related_models)

    # RelatedSSR
#    if relatedssrdisp and related_ssrs and len(related_ssrs) :
#        section=related_ssr_section_rtf(section, ss, related_ssrs)

    # RelatedSED
#    if relatedseddisp and related_seds and len(related_seds) :
#        section=related_sed_section_rtf(section, ss, related_seds)

    # References
#    if referencedisp and references and len(references) :
#        section=reference_section_rtf(section, ss, references)

    return doc


def ssr_report_pdf(context, display_settings, elements=None):
    ##############################################################################
    if elements is None:
        elements = []

    elements.append(Paragraph('SSR: %s' % unicode(context['ssr'].title).encode('latin1','ignore'), styles['Heading1']))

    elements.append(Paragraph('Model: %s' % unicode(context['model']).encode('latin1','ignore'), styles['Heading1']))

    rows=0
    basicInfoData=[[Paragraph('Brief Description *',styles['Heading2']),
                    Paragraph(unicode(context['ssr'].brief_description).encode('latin1','ignore'), styles["BodyText"]),
                    '']]
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]
    tableStyle.append(('SPAN',(1,rows),(2,rows)))
    rows += 1

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['ssr'].narrative and len(context['ssr'].narrative):
        basicInfoData.append([Paragraph('Narrative *',styles['Heading2']),
                              Paragraph(unicode(context['ssr'].narrative).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))
        rows += 1

    # Tags
    basicInfoData.append([Paragraph('Tags',styles['Heading2']),
                          Paragraph(unicode(', '.join(context['ssr'].tags.names())).encode('latin1','ignore'),styles['BodyText']),
                          ''])
    tableStyle.append(('SPAN',(1,rows),(2,rows)))

    t=reportlab.platypus.tables.Table(basicInfoData, [1.5*inch, inch, 5*inch],
        style=tableStyle)
    elements.append(t)

    #print figures
    if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
        elements=figure_section_pdf(elements, context['figures'])

    # RelatedModel
#    if relatedmodeldisp and related_models and len(related_models) :
#        elements=related_model_section_pdf(elements, related_models)

    # RelatedSSR
#    if relatedssrdisp and related_ssrs and len(related_ssrs) :
#        elements=related_ssr_section_pdf(elements, related_ssrs)

    # RelatedSED
#    if relatedseddisp and related_seds and len(related_seds) :
#        elements=related_sed_section_pdf(elements, related_seds)

    # References
#    if referencedisp and references and len(references) :
#        elements=reference_section_pdf(elements, references)

    return elements

def sed_report_rtf(context, display_settings, doc=None):
    # Create the document
    if doc is None:
        doc = PyRTF.Elements.Document()
    ss = doc.StyleSheet
    NormalText = TextStyle( TextPropertySet( ss.Fonts.Arial, 22 ) )
    NormalText.TextPropertySet.SetSize(22).SetBold(True).SetUnderline(False).SetItalic(False)
    ps = ParagraphStyle( 'Heading 5', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(24).SetBold(True).SetUnderline(True).SetItalic(False)
    ps = ParagraphStyle( 'Heading 4', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(26).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 3', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(28).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 2', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(32).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 1', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    section = Section()
    doc.Sections.append( section )

    #print sed title
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading1)
    p.append(unicode('SED: %s' % context['sed'].title).encode('latin1','ignore'))
    section.append(p)

    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 6 )
    table.SetGapBetweenCells(0)

    #print sed description
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Brief Description *'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(context['sed'].brief_description).encode('latin1','ignore')), thin_frame)
    c2.SetSpan(2)
    table.AddRow(c1, c2)

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['sed'].narrative and len(context['sed'].narrative):
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Narrative *'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(context['sed'].narrative).encode('latin1','ignore')), thin_frame)
        c2.SetSpan(2)
        table.AddRow(c1, c2)

    # Tags
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Tags'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(', '.join(context['sed'].tags.names())).encode('latin1','ignore')), thin_frame)
    c2.SetSpan(2)
    table.AddRow(c1, c2)

    if BrainImagingSED.objects.filter(id=context['sed'].id):
        imagingSED=BrainImagingSED.objects.get(id=context['sed'].id)

        # Method
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Method *'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(imagingSED.method).encode('latin1','ignore')), thin_frame)
        c2.SetSpan(2)
        table.AddRow(c1, c2)

        # Control condition
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Control Condition'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(imagingSED.control_condition).encode('latin1','ignore')), thin_frame)
        c2.SetSpan(2)
        table.AddRow(c1, c2)

        # Experimental condition
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Experimental Condition *'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(imagingSED.experimental_condition).encode('latin1','ignore')), thin_frame)
        c2.SetSpan(2)
        table.AddRow(c1, c2)

    section.append(table)

    if BrainImagingSED.objects.filter(id=context['sed'].id):
        p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
        p.append("Data")
        section.append(p)

        imagingSED=BrainImagingSED.objects.get(id=context['sed'].id)
        coords=SEDCoord.objects.filter(sed__id=context['sed'].id)

        table = PyRTF.Table()
        table.SetGapBetweenCells(0)

        region_span=TabPS.DEFAULT_WIDTH * 4
        region_header=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,'Brain Region'), thin_frame)
        hemi_span=TabPS.DEFAULT_WIDTH * 2
        hemi_header=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,'Hemisphere'), thin_frame)

        header_str=imagingSED.core_header_1+' | '+imagingSED.core_header_2+' | '+imagingSED.core_header_3 + ' | '+imagingSED.core_header_4
        core_header_elems=[x.strip() for x in header_str.split('|')]
        extra_header_elems=[x.strip() for x in imagingSED.extra_header.split('|')]
        all_header_elems=[]
        all_header_elems.extend(core_header_elems)
        all_header_elems.extend(extra_header_elems)

        spans=[region_span, hemi_span]
        headers=[region_header, hemi_header]
        for elem in all_header_elems:
            if not elem=='hemisphere' and not elem=='N/A':
                extra_span=TabPS.DEFAULT_WIDTH
                extra_header=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(elem).encode('latin1','ignore')), thin_frame)
                spans.append(extra_span)
                headers.append(extra_header)

        table.SetColumnWidths(*spans)
        table.AddRow(*headers)

        for coord in coords:
            region_cell = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.named_brain_region).encode('latin1','ignore')), thin_frame)
            hemi_cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.hemisphere).encode('latin1','ignore')), thin_frame)
            cells=[region_cell,hemi_cell]

            for col in core_header_elems:
                if col=='x':
                    x_cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.coord.x).encode('latin1','ignore')), thin_frame)
                    cells.append(x_cell)
                elif col=='y':
                    y_cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.coord.y).encode('latin1','ignore')), thin_frame)
                    cells.append(y_cell)
                elif col=='z':
                    z_cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.coord.z).encode('latin1','ignore')), thin_frame)
                    cells.append(z_cell)
                elif col=='rCBF':
                    rCBF_cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.rcbf).encode('latin1','ignore')), thin_frame)
                    cells.append(rCBF_cell)
                elif col=='T' or col=='Z':
                    stat_cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(coord.statistic_value).encode('latin1','ignore')), thin_frame)
                    cells.append(stat_cell)

            extra_cols=[x.strip() for x in coord.extra_data.split('|')]
            for col in extra_cols:
                cell=Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(col).encode('latin1','ignore')),thin_frame)
                cells.append(cell)

            table.AddRow(*cells)

        section.append(table)

    #print figures
    if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
        section=figure_section_rtf(section, ss, context['figures'])

    # RelatedBOP
    if display_settings['relatedbopdisp'] and context['related_bops'] and len(context['related_bops']) :
        section=related_bop_section_rtf(section, ss, context['related_bops'], False)

    # RelatedModel
    if display_settings['relatedmodeldisp'] and context['related_models'] and len(context['related_models']) :
        section=related_model_section_rtf(section, ss, context['related_models'])

    # RelatedSED
#    if display_settings['relatedseddisp'] and context['related_seds'] and len(context['related_seds']) :
#        section=related_sed_section_rtf(section, ss, context['related_seds'])

    # RelatedSSR
#    if display_settings['relatedssrdisp'] and context['related_ssrs'] and len(context['related_ssrs']) :
#        section=related_ssr_section_rtf(section, ss, context['related_ssrs'])

    # RelatedBrainRegion
    if display_settings['relatedregiondisp'] and context['related_brain_regions'] and len(context['related_brain_regions']):
        section=related_brain_region_section_rtf(section, ss, context['related_brain_regions'])

    # References
    if display_settings['referencedisp'] and context['references'] and len(context['references']) :
        reference_section_rtf(section, ss, context['references'])

    return doc


def sed_report_pdf(context, display_settings, elements=None):
    if elements is None:
        elements = []

    elements.append(Paragraph('SED: %s' % unicode(context['sed'].title).encode('latin1','ignore'), styles['Heading1']))

    rows=0
    basicInfoData=[[Paragraph('Brief Description *',styles['Heading2']),
                    Paragraph(unicode(context['sed'].brief_description).encode('latin1','ignore'), styles["BodyText"]),
                    '']]
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]
    tableStyle.append(('SPAN',(1,rows),(2,rows)))
    rows += 1

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['sed'].narrative and len(context['sed'].narrative):
        basicInfoData.append([Paragraph('Narrative *',styles['Heading2']),
                              Paragraph(unicode(context['sed'].narrative).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))
        rows += 1

    # Tags
    basicInfoData.append([Paragraph('Tags',styles['Heading2']),
                          Paragraph(unicode(', '.join(context['sed'].tags.names())).encode('latin1','ignore'),styles['BodyText']),
                          ''])
    tableStyle.append(('SPAN',(1,rows),(2,rows)))
    rows += 1

    if BrainImagingSED.objects.filter(id=context['sed'].id):
        imagingSED=BrainImagingSED.objects.get(id=context['sed'].id)

        # Method
        basicInfoData.append([Paragraph('Method *',styles['Heading2']),
                              Paragraph(unicode(imagingSED.method).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))
        rows += 1

        # Control condition
        basicInfoData.append([Paragraph('Control Condition',styles['Heading2']),
                              Paragraph(unicode(imagingSED.control_condition).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))
        rows += 1

        # Experimental condition
        basicInfoData.append([Paragraph('Experimental Condition *',styles['Heading2']),
                              Paragraph(unicode(imagingSED.experimental_condition).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))

    t=reportlab.platypus.tables.Table(basicInfoData, [1.5*inch, inch, 5*inch], style=tableStyle)
    elements.append(t)

    if BrainImagingSED.objects.filter(id=context['sed'].id):
        imagingSED=BrainImagingSED.objects.get(id=context['sed'].id)
        coords=SEDCoord.objects.filter(sed__id=context['sed'].id)

        elements.append(Paragraph('Data', styles['Heading2']))
        coordData=[]
        tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP')]

        header=[Paragraph('Brain Region',styles['Heading4']),
                Paragraph('Hemisphere',styles['Heading4'])]
        col_width=[1.5*inch, inch]
        header_str=imagingSED.core_header_1+' | '+imagingSED.core_header_2+' | '+imagingSED.core_header_3 + ' | '+imagingSED.core_header_4
        core_header_elems=[x.strip() for x in header_str.split('|')]
        extra_header_elems=[x.strip() for x in imagingSED.extra_header.split('|')]
        all_header_elems=[]
        all_header_elems.extend(core_header_elems)
        all_header_elems.extend(extra_header_elems)

        for elem in all_header_elems:
            if not elem=='hemisphere' and not elem=='N/A':
                col_width.append(inch)
                header.append(Paragraph(elem,styles['Heading4']))
        coordData.append(header)
        rows=1

        for coord in coords:
            cols=[]
            cols.append(Paragraph(unicode(coord.named_brain_region).encode('latin1','ignore'),styles['BodyText']))
            cols.append(Paragraph(unicode(coord.hemisphere).encode('latin1','ignore'),styles['BodyText']))

            for col in core_header_elems:
                if col=='x':
                    cols.append(Paragraph(unicode(coord.coord.x).encode('latin1','ignore'),styles['BodyText']))
                elif col=='y':
                    cols.append(Paragraph(unicode(coord.coord.y).encode('latin1','ignore'),styles['BodyText']))
                elif col=='z':
                    cols.append(Paragraph(unicode(coord.coord.z).encode('latin1','ignore'),styles['BodyText']))
                elif col=='rCBF':
                    cols.append(Paragraph(unicode(coord.rcbf).encode('latin1','ignore'),styles['BodyText']))
                elif col=='T' or col=='Z':
                    cols.append(Paragraph(unicode(coord.statistic_value).encode('latin1','ignore'),styles['BodyText']))
            extra_cols=[x.strip() for x in coord.extra_data.split('|')]
            for col in extra_cols:
                cols.append(Paragraph(unicode(col).encode('latin1','ignore'),styles['BodyText']))
            coordData.append(cols)
            rows += 1

        t=reportlab.platypus.tables.Table(coordData, col_width, style=tableStyle)
        elements.append(t)

    #print figures
    if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
        elements=figure_section_pdf(elements, context['figures'])

    # RelatedBOP
    if display_settings['relatedbopdisp'] and context['related_bops'] and len(context['related_bops']) :
        elements=related_bop_section_pdf(elements, context['related_bops'], False)

    # RelatedModel
    if display_settings['relatedmodeldisp'] and context['related_models'] and len(context['related_models']) :
        elements=related_model_section_pdf(elements, context['related_models'])

    # RelatedSED
#    if display_settings['relatedseddisp'] and context['related_seds'] and len(context['related_seds']) :
#        elements=related_sed_section_pdf(elements, context['related_seds'])

    # RelatedSSR
#    if display_settings['relatedssrdisp'] and context['related_ssrs'] and len(context['related_ssrs']) :
#        elements=related_ssr_section_pdf(elements, context['related_ssrs'])

    # RelatedBrainRegion
    if display_settings['relatedregiondisp'] and context['related_brain_regions'] and len(context['related_brain_regions']):
        elements=related_brain_region_section_pdf(elements, context['related_brain_regions'])

    # References
    if display_settings['referencedisp'] and context['references'] and len(context['references']) :
        elements=reference_section_pdf(elements, context['references'])

    return elements


def model_report_rtf(context, display_settings, doc=None):


    ##############################################################################

    # Create the document
    if doc is None:
        doc = PyRTF.Elements.Document()
    ss = doc.StyleSheet
    NormalText = TextStyle( TextPropertySet( ss.Fonts.Arial, 22 ) )
    NormalText.TextPropertySet.SetSize(22).SetBold(True).SetUnderline(False).SetItalic(False)
    ps = ParagraphStyle( 'Heading 5', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(24).SetBold(True).SetUnderline(True).SetItalic(False)
    ps = ParagraphStyle( 'Heading 4', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(26).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 3', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(28).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 2', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(32).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 1', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    section = Section()
    doc.Sections.append( section )

    #print model title
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading1)
    p.append('Model: %s' % unicode(context['model'].title).encode('latin1','replace'))
    section.append(p)

    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 6 )
    table.SetGapBetweenCells(0)
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Authors'), thin_frame)
    c1.SetSpan(3)
    table.AddRow(c1)

    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'First name'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Middle name'), thin_frame)
    c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Last name'), thin_frame)
    table.AddRow(c1, c2, c3)

    for author in context['model'].authors.all() :
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(author.author.first_name).encode('latin1','replace')), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(author.author.middle_name).encode('latin1','replace')), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(author.author.last_name).encode('latin1','replace')), thin_frame)
        table.AddRow(c1, c2, c3)

    #print model description
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Brief Description *'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(context['model'].brief_description).encode('latin1','replace')), thin_frame)
    c2.SetSpan(2)
    table.AddRow(c1, c2)

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['model'].narrative and len(context['model'].narrative):
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Narrative *'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal, unicode(context['model'].narrative).encode('latin1','replace')), thin_frame)
        c2.SetSpan(2)
        table.AddRow(c1, c2)

    # Tags
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Tags'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(', '.join(context['model'].tags.names())).encode('latin1','replace')), thin_frame)
    c2.SetSpan(2)
    table.AddRow(c1, c2)

    section.append(table)

    if (display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures'])) or\
       (context['input_ports'] and len(context['input_ports'])) or\
       (context['output_ports'] and len(context['output_ports'])) or (context['states'] and len(context['states'])) or\
       (context['modules'] and len(context['modules'])):
        #print architecture
        p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
        p.append("Architecture")
        section.append(p)

        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 6 )

        if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Diagrams'), thin_frame)
            c1.SetSpan(3)
            table.AddRow(c1)

            for figure in context['figures']:
                thumb_path=get_thumbnail(figure.figure.path, figure.figure.width, figure.figure.height)
                image = PyRTF.Image(thumb_path)
                c1 = Cell(PyRTF.Paragraph(image))
                c1.SetSpan(2)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(figure.caption).encode('latin1','replace')), thin_frame)
                table.AddRow(c1, c2)

        #print architecture.inputs
        if context['input_ports'] and len(context['input_ports']):
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Inputs'), thin_frame)
            c1.SetSpan(3)
            table.AddRow(c1)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Data Type'), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            table.AddRow(c1, c2, c3)

            for input in context['input_ports']:
                c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(input.name).encode('latin1','replace')), thin_frame)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(input.data_type).encode('latin1','replace')), thin_frame)
                c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(input.description).encode('latin1','replace')), thin_frame)
                table.AddRow(c1, c2, c3)

        #print architecture.outputs
        if context['output_ports'] and len(context['output_ports']):
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Outputs'), thin_frame)
            c1.SetSpan(3)
            table.AddRow(c1)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Data Type'), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            table.AddRow(c1, c2, c3)

            for output in context['output_ports']:
                c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(output.name).encode('latin1','replace')), thin_frame)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(output.data_type).encode('latin1','replace')), thin_frame)
                c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(output.description).encode('latin1','replace')), thin_frame)
                table.AddRow(c1, c2, c3)

        #print architecture.states
        if context['states'] and len(context['states']):
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'States'), thin_frame)
            c1.SetSpan(3)
            table.AddRow(c1)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Data Type'), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            table.AddRow(c1, c2, c3)

            for state in context['states']:
                c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(state.name).encode('latin1','replace')), thin_frame)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(state.data_type).encode('latin1','replace')), thin_frame)
                c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(state.description).encode('latin1','replace')), thin_frame)
                table.AddRow(c1, c2, c3)

        if context['modules'] and len(context['modules']):
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Submodules'), thin_frame)
            c1.SetSpan(3)
            table.AddRow(c1)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            c2.SetSpan(2)
            table.AddRow(c1, c2)

            for module in context['modules']:
                c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(module.module.title).encode('latin1','replace')), thin_frame)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(module.module.brief_description).encode('latin1','replace')), thin_frame)
                c2.SetSpan(2)
                table.AddRow(c1, c2)

        section.append(table)

    # SED + SSR
    if display_settings['seddisp'] == 1:
        p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
        p.append("Summaries of Experimental Data (SEDs) and Simulation Results (SSRs)")
        section.append(p)

        #SED
        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 3 )
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'SEDs used to build the model'), thin_frame)
        c1.SetSpan(4)
        table.AddRow(c1)

        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relationship'), thin_frame)
        c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relevance Narrative'), thin_frame)
        table.AddRow(c1, c2, c3, c4)

        for buildsed in context['building_seds'] :
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.sed.title).encode('latin1','replace')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.sed.brief_description).encode('latin1','replace')), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.relationship).encode('latin1','replace')), thin_frame)
            c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.relevance_narrative).encode('latin1','replace')), thin_frame)
            table.AddRow(c1, c2, c3, c4)

        #SED for testing
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'SEDs used to test the model'), thin_frame)
        c1.SetSpan(4)
        table.AddRow(c1)

        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relationship'), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relevance Narrative'), thin_frame)
        c3.SetSpan(2)
        table.AddRow(c1, c2, c3)

        for testsed in context['testing_seds'] :
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(testsed.relationship).encode('latin1','replace')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(testsed.relevance_narrative).encode('latin1','replace')), thin_frame)
            c1.SetSpan(2)
            c2.SetSpan(2)
            table.AddRow(c1, c2)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetStartVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'SED'), thin_frame)
            c2.SetSpan(3)
            table.AddRow(c1,c2)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            c3.SetSpan(2)
            table.AddRow(c1, c2, c3)

            if testsed.sed:
                c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
                c1.SetVerticalMerge(True)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(testsed.sed.title).encode('latin1','replace')), thin_frame)
                c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(testsed.sed.brief_description).encode('latin1','replace')), thin_frame)
                c3.SetSpan(2)
                table.AddRow(c1,c2,c3)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetStartVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'SSR'), thin_frame)
            c2.SetSpan(3)
            table.AddRow(c1,c2)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            c3.SetSpan(2)
            table.AddRow(c1, c2, c3)

            if testsed.get_ssr():
                c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
                c1.SetVerticalMerge(True)
                c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(testsed.get_ssr().title).encode('latin1','ignore')), thin_frame)
                c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(testsed.get_ssr().brief_description).encode('latin1','replace')), thin_frame)
                c3.SetSpan(2)
                table.AddRow(c1,c2,c3)

        # Prediction SSRs
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Predictions'), thin_frame)
        c1.SetSpan(4)
        table.AddRow(c1)

        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
        c2.SetSpan(3)
        table.AddRow(c1, c2)

        for prediction in context['predictions'] :
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(prediction.title).encode('latin1','ignore')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(prediction.brief_description).encode('latin1','ignore')), thin_frame)
            c2.SetSpan(3)
            table.AddRow(c1, c2)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetStartVerticalMerge(True)
            c1.SetVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'SSR'), thin_frame)
            c2.SetSpan(3)
            table.AddRow(c1,c2)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
            c3.SetSpan(2)
            table.AddRow(c1, c2, c3)

            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,''), thin_frame)
            c1.SetVerticalMerge(True)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(prediction.get_ssr().title).encode('latin1','ignore')), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(prediction.get_ssr().brief_description).encode('latin1','ignore')), thin_frame)
            c3.SetSpan(2)
            table.AddRow(c1,c2,c3)

        section.append(table)

    # URLs
    if display_settings['urldisp'] == 1:
        p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
        p.append("URLs")
        section.append(p)

        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 10)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Execution URL:'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(context['model'].execution_url).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Documentation URL:'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(context['model'].documentation_url).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description URL:'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(context['model'].description_url).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Simulation URL:'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(context['model'].simulation_url).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)
        section.append(table)


    # RelatedModel
    if display_settings['relatedmodeldisp'] and context['related_models'] and len(context['related_models']) :
        section=related_model_section_rtf(section, ss, context['related_models'])

    # RelatedBOP
    if display_settings['relatedbopdisp'] and context['related_bops'] and len(context['related_bops']) :
        section=related_bop_section_rtf(section, ss, context['related_bops'], False)

    # RelatedBrainRegion
    if display_settings['relatedregiondisp'] and context['related_brain_regions'] and len(context['related_brain_regions']):
        section=related_brain_region_section_rtf(section, ss, context['related_brain_regions'])

    # References
    if display_settings['referencedisp'] and context['references'] and len(context['references']) :
        reference_section_rtf(section, ss, context['references'])

    return doc


def model_report_pdf(context, display_settings, elements=None):
    ##############################################################################
    if elements is None:
        elements = []

    elements.append(Paragraph('Model: %s' % context['model'].title, styles['Heading1'], encoding='latin1'))

    rows=0
    basicInfoData = [[Paragraph('Authors',styles['Heading2']),'',''],
                     [Paragraph('First name',styles['Heading3']),
                      Paragraph('Middle name',styles['Heading3']),
                      Paragraph('Last name',styles['Heading3'])]]
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]
    rows += 2
    tableStyle.append(('SPAN',(0,0),(2,0)))
    for author in context['model'].authors.all():
        basicInfoData.append([Paragraph(unicode(author.author.first_name).encode('latin1','ignore'),styles['BodyText']),
                              Paragraph(unicode(author.author.middle_name).encode('latin1','ignore'),styles['BodyText']),
                              Paragraph(unicode(author.author.last_name).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1

    basicInfoData.append([Paragraph('Brief Description *',styles['Heading2']),
                          Paragraph(unicode(context['model'].brief_description).encode('latin1','ignore'), styles["BodyText"]),
                          ''])
    tableStyle.append(('SPAN',(1,rows),(2,rows)))
    rows += 1

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['model'].narrative and len(context['model'].narrative):
        basicInfoData.append([Paragraph('Narrative *',styles['Heading2']),
                              Paragraph(unicode(context['model'].narrative).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))
        rows += 1

    # Tags
    basicInfoData.append([Paragraph('Tags',styles['Heading2']),
                          Paragraph(unicode(', '.join(context['model'].tags.names())).encode('latin1','ignore'),styles['BodyText']),
                          ''])
    tableStyle.append(('SPAN',(1,rows),(2,rows)))

    t=reportlab.platypus.tables.Table(basicInfoData, [1.5*inch, inch, 5*inch],
        style=tableStyle)
    elements.append(t)

    #print architecture
    if (display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures'])) or \
       (context['input_ports'] and len(context['input_ports'])) or \
       (context['output_ports'] and len(context['output_ports'])) or (context['states'] and len(context['states'])) or \
       (context['modules'] and len(context['modules'])):
        elements.append(Paragraph('Architecture', styles['Heading2']))
        architectureData=[]
        rows=0
        tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP')]

        if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
            architectureData.append([Paragraph('Diagrams',styles['Heading2']),'',''])
            tableStyle.append(('SPAN',(0,0),(2,0)))
            rows += 1

            for figure in context['figures']:
                thumb_path=get_thumbnail(figure.figure.path, figure.figure.width, figure.figure.height)
                image = Image(thumb_path)
                architectureData.append([image,
                                         '',
                                         Paragraph(unicode(figure.caption).encode('latin1','ignore'), styles['BodyText'])])
                tableStyle.append(('SPAN',(0,rows),(1,rows)))
                rows += 1

        #print architecture.inputs
        if context['input_ports'] and len(context['input_ports']):
            architectureData.append([Paragraph('Inputs',styles['Heading2']),'',''])
            tableStyle.append(('SPAN',(0,rows),(2,rows)))
            rows += 1

            architectureData.append([Paragraph('Name',styles['Heading3']),
                                     Paragraph('Data Type',styles['Heading3']),
                                     Paragraph('Description',styles['Heading3'])])
            rows += 1

            for input in context['input_ports']:
                architectureData.append([Paragraph(unicode(input.name).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(input.data_type).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(input.description).encode('latin1','ignore'),styles['BodyText'])])
                rows += 1

        #print architecture.outputs
        if context['output_ports'] and len(context['output_ports']):
            architectureData.append([Paragraph('Outputs',styles['Heading2']),'',''])
            tableStyle.append(('SPAN',(0,rows),(2,rows)))
            rows += 1

            architectureData.append([Paragraph('Name',styles['Heading3']),
                                     Paragraph('Data Type',styles['Heading3']),
                                     Paragraph('Description',styles['Heading3'])])
            rows += 1

            for output in context['output_ports']:
                architectureData.append([Paragraph(unicode(output.name).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(output.data_type).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(output.description).encode('latin1','ignore'),styles['BodyText'])])
                rows += 1

        #print architecture.states
        if context['states'] and len(context['states']):
            architectureData.append([Paragraph('States',styles['Heading2']),'',''])
            tableStyle.append(('SPAN',(0,rows),(2,rows)))
            rows += 1

            architectureData.append([Paragraph('Name',styles['Heading3']),
                                     Paragraph('Data Type',styles['Heading3']),
                                     Paragraph('Description',styles['Heading3'])])
            rows += 1

            for state in context['states']:
                architectureData.append([Paragraph(unicode(state.name).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(state.data_type).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(state.description).encode('latin1','ignore'),styles['BodyText'])])
                rows += 1

        if context['modules'] and len(context['modules']):
            architectureData.append([Paragraph('Submodules',styles['Heading2']),'',''])
            tableStyle.append(('SPAN',(0,rows),(2,rows)))
            rows += 1

            architectureData.append([Paragraph('Name',styles['Heading3']),
                                     Paragraph('Description',styles['Heading3']),''])
            tableStyle.append(('SPAN',(1,rows),(2,rows)))
            rows += 1

            for module in context['modules']:
                architectureData.append([Paragraph(unicode(module.module.title).encode('latin1','ignore'),styles['BodyText']),
                                         Paragraph(unicode(module.module.brief_description).encode('latin1','ignore'),styles['BodyText']),''])
                tableStyle.append(('SPAN',(1,rows),(2,rows)))
                rows += 1

        t=reportlab.platypus.tables.Table(architectureData, [2.25*inch, 2.25*inch, 3*inch],
            style=tableStyle)
        elements.append(t)

    # SED + SSR
    if display_settings['seddisp'] == 1:
        elements.append(Paragraph('Summaries of Experimental Data (SEDs) and Simulation Results (SSRs)', styles['Heading2']))
        sedData=[]
        rows=0
        tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP')]

        #SED
        sedData.append([Paragraph('SEDs used to build the model',styles['Heading2']),'','',''])
        tableStyle.append(('SPAN',(0,rows),(3,rows)))
        rows += 1

        sedData.append([Paragraph('Name',styles['Heading3']),
                        Paragraph('Description',styles['Heading3']),
                        Paragraph('Relationship',styles['Heading3']),
                        Paragraph('Relevance Narrative',styles['Heading3'])])
        rows += 1

        for buildsed in context['building_seds']:
            sedData.append([Paragraph(unicode(buildsed.sed.title).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(buildsed.sed.brief_description).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(buildsed.relationship).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(buildsed.relevance_narrative).encode('latin1','ignore'),styles['BodyText'])])
            rows += 1

        #SED for testing
        sedData.append([Paragraph('SEDs used to test the model',styles['Heading2']),'','',''])
        tableStyle.append(('SPAN',(0,rows),(3,rows)))
        rows += 1

        sedData.append([Paragraph('Name',styles['Heading3']),
                        Paragraph('Relationship',styles['Heading3']),
                        Paragraph('Relevance Narrative',styles['Heading3']),''])
        tableStyle.append(('SPAN',(2,rows),(3,rows)))
        rows += 1

        for testsed in context['testing_seds'] :
            sedData.append([Paragraph(unicode(testsed.relationship).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(testsed.relevance_narrative).encode('latin1','ignore'),styles['BodyText']),''])
            tableStyle.append(('SPAN',(2,rows),(3,rows)))
            rows += 1

            sedData.append(['',
                            Paragraph('SED',styles['Heading2']),
                            '',
                            ''])
            tableStyle.append(('SPAN',(1,rows),(3,rows)))
            rows += 1

            sedData.append(['',
                            Paragraph('Name',styles['Heading3']),
                            Paragraph('Description',styles['Heading3']),
                            ''])
            tableStyle.append(('SPAN',(2,rows),(3,rows)))
            rows += 1

            if testsed.sed:
                sedData.append(['',
                                Paragraph(unicode(testsed.sed.title).encode('latin1','ignore'),styles['BodyText']),
                                Paragraph(unicode(testsed.sed.brief_description).encode('latin1','ignore'),styles['BodyText']),
                                ''])
                tableStyle.append(('SPAN',(2,rows),(3,rows)))
                rows += 1

            sedData.append(['',
                            Paragraph('SSR',styles['Heading2']),
                            '',
                            ''])
            tableStyle.append(('SPAN',(1,rows),(3,rows)))
            rows += 1

            sedData.append(['',
                            Paragraph('Name',styles['Heading3']),
                            Paragraph('Description',styles['Heading3']),
                            ''])
            tableStyle.append(('SPAN',(2,rows),(3,rows)))
            rows += 1

            if testsed.get_ssr():
                sedData.append(['',
                                Paragraph(unicode(testsed.get_ssr().title).encode('latin1','ignore'),styles['BodyText']),
                                Paragraph(unicode(testsed.get_ssr().brief_description).encode('latin1','ignore'),styles['BodyText']),
                                ''])
                tableStyle.append(('SPAN',(2,rows),(3,rows)))
                rows += 1

        # Prediction SSRs
        sedData.append([Paragraph('Predictions',styles['Heading2']),
                        '',
                        '',
                        ''])
        tableStyle.append(('SPAN',(0,rows),(3,rows)))
        rows += 1

        sedData.append([Paragraph('Name',styles['Heading3']),
                        Paragraph('Description',styles['Heading3']),
                        '',
                        ''])
        tableStyle.append(('SPAN',(1,rows),(3,rows)))
        rows += 1

        for prediction in context['predictions'] :
            sedData.append([Paragraph(unicode(prediction.title).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(prediction.brief_description).encode('latin1','ignore'),styles['BodyText']),
                            '',
                            ''])
            tableStyle.append(('SPAN',(1,rows),(3,rows)))
            rows += 1

            sedData.append(['',
                            Paragraph('SSR',styles['Heading2']),
                            '',
                            ''])
            tableStyle.append(('SPAN',(1,rows),(3,rows)))
            rows += 1

            sedData.append(['',
                            Paragraph('Name',styles['Heading3']),
                            Paragraph('Description',styles['Heading3']),
                            ''])
            tableStyle.append(('SPAN',(2,rows),(3,rows)))
            rows += 1

            sedData.append(['',
                            Paragraph(unicode(prediction.get_ssr().title).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(prediction.get_ssr().brief_description).encode('latin1','ignore'),styles['BodyText']),
                            ''])
            tableStyle.append(('SPAN',(2,rows),(3,rows)))
            rows += 1

        t=reportlab.platypus.tables.Table(sedData, [1.5*inch, 2*inch, 2*inch, 2*inch],
            style=tableStyle)
        elements.append(t)

    # URLs
    if display_settings['urldisp'] == 1:
        elements.append(Paragraph('URLs', styles['Heading2']))
        urlData=[]
        rows=0
        tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP')]

        urlData.append([Paragraph('Execution URL',styles['Heading3']),
                        Paragraph(unicode(context['model'].execution_url).encode('latin1','ignore'),styles['BodyText'])])
        #tableStyle.append(('SPAN',(1,rows),(3,rows)))
        rows += 1

        urlData.append([Paragraph('Documentation URL',styles['Heading3']),
                        Paragraph(unicode(context['model'].documentation_url).encode('latin1','ignore'),styles['BodyText'])])
        #tableStyle.append(('SPAN',(1,rows),(3,rows)))
        rows += 1

        urlData.append([Paragraph('Description URL',styles['Heading3']),
                        Paragraph(unicode(context['model'].description_url).encode('latin1','ignore'),styles['BodyText'])])
        #tableStyle.append(('SPAN',(1,rows),(3,rows)))
        rows += 1

        urlData.append([Paragraph('Simulation URL',styles['Heading3']),
                        Paragraph(unicode(context['model'].simulation_url).encode('latin1','ignore'),styles['BodyText'])])
        #tableStyle.append(('SPAN',(1,rows),(3,rows)))
        rows+=1

        t=reportlab.platypus.tables.Table(urlData, [1.5*inch, 6*inch],
            style=tableStyle)
        elements.append(t)



    # RelatedModel
    if display_settings['relatedmodeldisp'] and context['related_models'] and len(context['related_models']) :
        elements=related_model_section_pdf(elements, context['related_models'])

    # RelatedBOP
    if display_settings['relatedbopdisp'] and context['related_bops'] and len(context['related_bops']) :
        elements=related_bop_section_pdf(elements, context['related_bops'], False)

    # RelatedBrainRegion
    if display_settings['relatedregiondisp'] and context['related_brain_regions'] and len(context['related_brain_regions']):
        elements=related_brain_region_section_pdf(elements, context['related_brain_regions'])

    # References
    if display_settings['referencedisp'] and context['references'] and len(context['references']) :
        elements=reference_section_pdf(elements, context['references'])

    return elements


def bop_report_rtf(context, display_settings, doc=None):

    ##############################################################################
    # Create the PDF object, using the response object as its "file."
    # set up Canvas
    if doc is None:
        doc = PyRTF.Elements.Document()
    ss = doc.StyleSheet
    NormalText = TextStyle( TextPropertySet( ss.Fonts.Arial, 22 ) )
    NormalText.TextPropertySet.SetSize(22).SetBold(True).SetUnderline(False).SetItalic(False)
    ps = ParagraphStyle( 'Heading 5', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(24).SetBold(True).SetUnderline(True).SetItalic(False)
    ps = ParagraphStyle( 'Heading 4', NormalText.Copy(), ParagraphPropertySet( space_before = 60, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(26).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 3', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(28).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 2', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    NormalText.TextPropertySet.SetSize(32).SetBold(True).SetItalic(False).SetUnderline(False)
    ps = ParagraphStyle( 'Heading 1', NormalText.Copy(), ParagraphPropertySet( space_before = 240, space_after  = 60 ) )
    ss.ParagraphStyles.append(ps)
    section = Section()
    doc.Sections.append( section )

    #print model title
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading1)
    p.append('BOP: %s' % unicode(context['bop'].title).encode('latin1','ignore'))
    section.append(p)

    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 9 )
    #print model description
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Brief Description *'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(context['bop'].brief_description).encode('latin1','ignore')), thin_frame)
    table.AddRow(c1, c2)

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['bop'].narrative and len(context['bop'].narrative):
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Narrative *'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(context['bop'].narrative).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)

    # Tags
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Tags'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(', '.join(context['bop'].tags.names())).encode('latin1','ignore')), thin_frame)
    table.AddRow(c1, c2)

    section.append(table)

    #print figures
    if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
        section=figure_section_rtf(section, ss, context['figures'])

    # ChildBOP
    if display_settings['childbopdisp'] and context['child_bops'] and len(context['child_bops']) :
        p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
        p.append("Child BOPs")
        section.append(p)
        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 9)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)

        table.AddRow(c1, c2)
        for child_bop in context['child_bops'] :
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(child_bop.title).encode('latin1','ignore')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(child_bop.brief_description).encode('latin1','ignore')), thin_frame)
            table.AddRow(c1, c2)
        section.append(table)

    # SED
    if display_settings['seddisp'] == 1:
        #SED
        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 3 )
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading4,'Summaries of Experimental Data (SEDs)'), thin_frame)
        c1.SetSpan(4)
        table.AddRow(c1)

        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relationship'), thin_frame)
        c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relevance Narrative'), thin_frame)

        table.AddRow(c1, c2, c3, c4)

        for buildsed in context['building_seds'] :
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.sed.title).encode('latin1','ignore')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.sed.brief_description).encode('latin1','ignore')), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.relationship).encode('latin1','ignore')), thin_frame)
            c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(buildsed.relevance_narrative).encode('latin1','ignore')), thin_frame)
            table.AddRow(c1, c2, c3, c4)

        section.append(table)

    # RelatedModel
    if display_settings['relatedmodeldisp'] and context['related_models'] and len(context['related_models']) :
        section=related_model_section_rtf(section, ss, context['related_models'])

    # RelatedBOP
    if display_settings['relatedbopdisp'] and context['related_bops'] and len(context['related_bops']) :
        section=related_bop_section_rtf(section, ss, context['related_bops'], True)

    # RelatedBrainRegion
    if display_settings['relatedregiondisp'] and context['related_brain_regions'] and len(context['related_brain_regions']):
        section=related_brain_region_section_rtf(section, ss, context['related_brain_regions'])

    # References
    if display_settings['referencedisp'] and context['references'] and len(context['references']) :
        section=reference_section_rtf(section, ss, context['references'])
    return doc


def bop_report_pdf(context, display_settings, elements=None):

    if elements is None:
        elements = []

    #print bop title
    elements.append(Paragraph('BOP: %s' % unicode(context['bop'].title).encode('latin1','ignore'), styles['Heading1']))

    rows=0
    basicInfoData=[[Paragraph('Brief Description *',styles['Heading2']),
                    Paragraph(unicode(context['bop'].brief_description).encode('latin1','ignore'), styles["BodyText"]),
                    '']]
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]
    tableStyle.append(('SPAN',(1,rows),(2,rows)))
    rows += 1

    # Narrative
    if display_settings['narrativedisp'] == 1 and context['bop'].narrative and len(context['bop'].narrative):
        basicInfoData.append([Paragraph('Narrative *',styles['Heading2']),
                              Paragraph(unicode(context['bop'].narrative).encode('latin1','ignore'),styles['BodyText']),
                              ''])
        tableStyle.append(('SPAN',(1,rows),(2,rows)))
        rows += 1

    # Tags
    basicInfoData.append([Paragraph('Tags',styles['Heading2']),
                          Paragraph(unicode(', '.join(context['bop'].tags.names())).encode('latin1','ignore'),styles['BodyText']),
                          ''])
    tableStyle.append(('SPAN',(1,rows),(2,rows)))

    t=reportlab.platypus.tables.Table(basicInfoData, [1.5*inch, inch, 5*inch], style=tableStyle)
    elements.append(t)

    #print figures    
    if display_settings['figuredisp'] == 1 and context['figures'] and len(context['figures']):
        elements=figure_section_pdf(elements, context['figures'])

    # ChildBOP
    if display_settings['childbopdisp'] and context['child_bops'] and len(context['child_bops']) :
        elements.append(Paragraph('Child BOPS', styles['Heading2']))
        bopData=[]
        rows=0
        tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP')]

        bopData.append([Paragraph('Name',styles['Heading3']),
                        Paragraph('Description',styles['Heading3'])])

        rows += 1

        for child_bop in context['child_bops'] :
            bopData.append([Paragraph(unicode(child_bop).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(child_bop.brief_description).encode('latin1','ignore'),styles['BodyText'])])
            rows += 1

        t=reportlab.platypus.tables.Table(bopData, [3*inch, 4.5*inch],
            style=tableStyle)
        elements.append(t)

    # SED
    if display_settings['seddisp'] == 1:
        elements.append(Paragraph('Summaries of Experimental Data (SEDs)', styles['Heading2']))
        sedData=[]
        rows=0
        tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP')]

        #SED
        sedData.append([Paragraph('Name',styles['Heading3']),
                        Paragraph('Description',styles['Heading3']),
                        Paragraph('Relationship',styles['Heading3']),
                        Paragraph('Relevance Narrative',styles['Heading3'])])
        rows += 1

        for buildsed in context['building_seds'] :
            sedData.append([Paragraph(unicode(buildsed.sed.title).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(buildsed.sed.brief_description).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(buildsed.relationship).encode('latin1','ignore'),styles['BodyText']),
                            Paragraph(unicode(buildsed.relevance_narrative).encode('latin1','ignore'),styles['BodyText'])])
            rows += 1

        t=reportlab.platypus.tables.Table(sedData, [1.5*inch, 2*inch, 2*inch, 2*inch],
            style=tableStyle)
        elements.append(t)


    # RelatedModel
    if display_settings['relatedmodeldisp'] and context['related_models'] and len(context['related_models']) :
        elements=related_model_section_pdf(elements, context['related_models'])

    # RelatedBOP
    if display_settings['relatedbopdisp'] and context['related_bops'] and len(context['related_bops']) :
        elements=related_bop_section_pdf(elements, context['related_bops'], True)

    # RelatedBrainRegion
    if display_settings['relatedregiondisp'] and context['related_brain_regions'] and len(context['related_brain_regions']):
        elements=related_brain_region_section_pdf(elements, context['related_brain_regions'])

    # References
    if display_settings['referencedisp'] and context['references'] and len(context['references']) :
        elements=reference_section_pdf(elements, context['references'])

    return elements


def related_model_section_rtf(section, ss, related_models):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("Related Models")
    section.append(p)
    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 5,TabPS.DEFAULT_WIDTH * 5)
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
    c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relationship'), thin_frame)
    table.AddRow(c1, c2, c3)
    for related_model in related_models :
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(str(related_model.model)).encode('latin1','ignore')), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_model.model.brief_description).encode('latin1','ignore')), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_model.relationship).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2, c3)
    section.append(table)

    return section


def related_model_section_pdf(elements, related_models):
    elements.append(Paragraph('Related Models', styles['Heading2']))
    modelData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]

    modelData.append([Paragraph('Name',styles['Heading3']),
                      Paragraph('Description',styles['Heading3']),
                      Paragraph('Relationship',styles['Heading3'])])
    rows += 1

    for related_model in related_models :
        modelData.append([Paragraph(unicode(str(related_model.model)).encode('latin1','ignore'),styles['BodyText']),
                          Paragraph(unicode(related_model.model.brief_description).encode('latin1','ignore'),styles['BodyText']),
                          Paragraph(unicode(related_model.relationship).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1

    t=reportlab.platypus.tables.Table(modelData, [1.5*inch, 4*inch, 2*inch],
        style=tableStyle)
    elements.append(t)

    return elements


def related_bop_section_rtf(section, ss, related_bops, bop_relationship):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("Related BOPs")
    section.append(p)
    if bop_relationship:
        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 2,TabPS.DEFAULT_WIDTH * 4)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relationship'), thin_frame)
        c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relevance Narrative'), thin_frame)
        table.AddRow(c1, c2, c3, c4)
    else:
        table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 5,TabPS.DEFAULT_WIDTH * 5)
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relevance Narrative'), thin_frame)
        table.AddRow(c1, c2, c3)

    for related_bop in related_bops :
        if bop_relationship:
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.bop.title).encode('latin1','ignore')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.bop.brief_description).encode('latin1','ignore')), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.relationship).encode('latin1','ignore')), thin_frame)
            c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.relevance_narrative).encode('latin1','ignore')), thin_frame)
            table.AddRow(c1, c2, c3, c4)
        else:
            c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.bop.title).encode('latin1','ignore')), thin_frame)
            c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.bop.brief_description).encode('latin1','ignore')), thin_frame)
            c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_bop.relevance_narrative).encode('latin1','ignore')), thin_frame)
            table.AddRow(c1, c2, c3)
    section.append(table)

    return section


def related_bop_section_pdf(elements, related_bops, bop_relationship):
    elements.append(Paragraph('Related BOPS', styles['Heading2']))
    bopData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]

    header=[Paragraph('Name',styles['Heading3']),
            Paragraph('Description',styles['Heading3'])]
    if bop_relationship:
        header.append(Paragraph('Relationship',styles['Heading3']))
    header.append(Paragraph('Relevance Narrative',styles['Heading3']))
    bopData.append(header)
    rows += 1

    for related_bop in related_bops :
        row=[Paragraph(related_bop.bop.title,styles['BodyText']),
             Paragraph(related_bop.bop.brief_description,styles['BodyText'])]
        if bop_relationship:
            row.append(Paragraph(related_bop.relationship,styles['BodyText']))
        row.append(Paragraph(related_bop.relevance_narrative,styles['BodyText']))
        bopData.append(row)
        rows += 1

    if bop_relationship:
        t=reportlab.platypus.tables.Table(bopData, [1.5*inch, 2.5*inch, 1*inch, 2.5*inch],
            style=tableStyle)
    else:
        t=reportlab.platypus.tables.Table(bopData, [1.5*inch, 3*inch, 3*inch],
            style=tableStyle)
    elements.append(t)

    return elements


def related_brain_region_section_rtf(section, ss, related_brain_regions):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("Related Brain Regions")
    section.append(p)
    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 2, TabPS.DEFAULT_WIDTH*2, TabPS.DEFAULT_WIDTH*3, TabPS.DEFAULT_WIDTH * 3)
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Type'), thin_frame)
    c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Nomenclature'), thin_frame)
    c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Species'), thin_frame)
    c5 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Relationship'), thin_frame)
    table.AddRow(c1, c2, c3, c4, c5)

    for related_brain_region in related_brain_regions :
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(str(related_brain_region.brain_region)).encode('latin1','ignore')), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_brain_region.brain_region.brain_region_type).encode('latin1','ignore')), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(str(related_brain_region.brain_region.nomenclature)).encode('latin1','ignore')), thin_frame)
        species_str=''
        for species in related_brain_region.brain_region.nomenclature.species.all():
            if len(species_str)>0:
                species_str += ', '
            species_str+=str(species)
        c4 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(species_str).encode('latin1','ignore')), thin_frame)
        c5 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_brain_region.relationship).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2, c3, c4, c5)
    section.append(table)

    return section


def related_brain_region_section_pdf(elements, related_brain_regions):
    elements.append(Paragraph('Related Brain Regions', styles['Heading2']))
    regionData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]

    regionData.append([Paragraph('Name',styles['Heading3']),
                       Paragraph('Type',styles['Heading3']),
                       Paragraph('Nomenclature',styles['Heading3']),
                       Paragraph('Relationship',styles['Heading3']),
                       Paragraph('Species',styles['Heading3'])])
    rows += 1

    for related_brain_region in related_brain_regions :
        species_str=''
        for species in related_brain_region.brain_region.nomenclature.species.all():
            if len(species_str)>0:
                species_str += ', '
            species_str+=str(species)
        regionData.append([Paragraph(unicode(str(related_brain_region.brain_region)).encode('latin1','ignore'),styles['BodyText']),
                           Paragraph(unicode(related_brain_region.brain_region.brain_region_type).encode('latin1','ignore'),styles['BodyText']),
                           Paragraph(unicode(str(related_brain_region.brain_region.nomenclature)).encode('latin1','ignore'),styles['BodyText']),
                           Paragraph(unicode(species_str).encode('latin1','ignore'),styles['BodyText']),
                           Paragraph(unicode(related_brain_region.relationship).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1

    t=reportlab.platypus.tables.Table(regionData, [1.5*inch, 1*inch, 1.5*inch, 1.5*inch, 2*inch],
        style=tableStyle)
    elements.append(t)

    return elements


def reference_section_rtf(section, ss, references):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("References")
    section.append(p)
    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 3,TabPS.DEFAULT_WIDTH * 2, TabPS.DEFAULT_WIDTH * 8)
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Authors'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Year'), thin_frame)
    c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Title'), thin_frame)
    table.AddRow(c1, c2, c3)

    for reference in references :
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(reference.author_names()).encode('latin1','ignore')), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(reference.year).encode('latin1','ignore')), thin_frame)
        c3 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(reference.title).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2, c3)
    section.append(table)

    return section


def reference_section_pdf(elements, references):
    elements.append(Paragraph('References', styles['Heading2']))
    referenceData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]

    referenceData.append([Paragraph('Authors',styles['Heading3']),
                          Paragraph('Year',styles['Heading3']),
                          Paragraph('Title',styles['Heading3'])])
    rows += 1

    for reference in references :
        referenceData.append([Paragraph(reference.author_names(),styles['BodyText'],encoding='latin1'),
                              Paragraph(unicode(reference.year),styles['BodyText'],encoding='latin1'),
                              Paragraph(unicode(reference.title).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1

    t=reportlab.platypus.tables.Table(referenceData, [2*inch, 1*inch, 4.5*inch], style=tableStyle)
    elements.append(t)

    return elements


def related_sed_section_rtf(section, ss, related_seds):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("Related SEDs")
    section.append(p)
    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 9)
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
    table.AddRow(c1, c2)
    for related_sed in related_seds :
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_sed.title).encode('latin1','ignore')), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_sed.brief_description).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)
    section.append(table)

    return section


def related_sed_section_pdf(elements, related_seds):
    elements.append(Paragraph('Related SEDs', styles['Heading2']))
    sedData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]

    sedData.append([Paragraph('Name',styles['Heading3']),
                    Paragraph('Description',styles['Heading3'])])
    rows += 1

    for related_sed in related_seds :
        sedData.append([Paragraph(unicode(related_sed.title).encode('latin1','ignore'),styles['BodyText']),
                        Paragraph(unicode(related_sed.brief_description).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1

    t=reportlab.platypus.tables.Table(sedData, [1.5*inch, 6*inch], style=tableStyle)
    elements.append(t)

    return elements


def related_ssr_section_rtf(section, ss, related_ssrs):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("Related SSRs")
    section.append(p)
    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 4,TabPS.DEFAULT_WIDTH * 9)
    c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Name'), thin_frame)
    c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Heading5,'Description'), thin_frame)
    table.AddRow(c1, c2)
    for related_ssr in related_ssrs :
        c1 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_ssr.title).encode('latin1','ignore')), thin_frame)
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(related_ssr.brief_description).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)
    section.append(table)

    return section


def related_ssr_section_pdf(elements, related_ssrs):
    elements.append(Paragraph('Related SSRs', styles['Heading2']))
    ssrData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]

    ssrData.append([Paragraph('Name',styles['Heading3']),
                    Paragraph('Description',styles['Heading3'])])
    rows += 1

    for related_ssr in related_ssrs :
        ssrData.append([Paragraph(unicode(related_ssr.title).encode('latin1','ignore'),styles['BodyText']),
                        Paragraph(unicode(related_ssr.brief_description).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1

    t=reportlab.platypus.tables.Table(ssrData, [1.5*inch, 6*inch],style=tableStyle)
    elements.append(t)

    return elements


def figure_section_rtf(section, ss, figures):
    p = PyRTF.Paragraph(ss.ParagraphStyles.Heading4)
    p.append("Figures")
    section.append(p)
    table = PyRTF.Table( TabPS.DEFAULT_WIDTH * 9, TabPS.DEFAULT_WIDTH * 4 )

    for figure in figures:
        thumb_path=get_thumbnail(figure.figure.path, figure.figure.width, figure.figure.height)
        image = PyRTF.Image(thumb_path)
        c1 = Cell(PyRTF.Paragraph(image))
        c2 = Cell(PyRTF.Paragraph(ss.ParagraphStyles.Normal,unicode(figure.caption).encode('latin1','ignore')), thin_frame)
        table.AddRow(c1, c2)

    section.append(table)

    return section

def figure_section_pdf(elements, figures):
    figureData=[]
    rows=0
    tableStyle=[('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('VALIGN',(0,0),(-1,-1),'TOP')]
    elements.append(Paragraph('Figures', styles['Heading2']))
    for figure in figures:
        thumb_path=get_thumbnail(figure.figure.path, figure.figure.width, figure.figure.height)
        image = Image(thumb_path)
        figureData.append([image,Paragraph(unicode(figure.caption).encode('latin1','ignore'),styles['BodyText'])])
        rows += 1
    t=reportlab.platypus.tables.Table(figureData, [4.25*inch, 3.25*inch], style=tableStyle)
    elements.append(t)

    return elements