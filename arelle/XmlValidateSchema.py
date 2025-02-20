'''
Created on Apr 10, 2013

@author: Mark V Systems Limited
(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
import time
from arelle import ModelXbrl, XbrlConst, XmlValidate
from arelle.ModelObject import ModelObject
from arelle.ModelDtsObject import ModelAttribute, ModelConcept, ModelType
from arelle.ModelValue import qname
from arelle.Locale import format_string
from lxml import etree

XMLSchemaURI = "http://www.w3.org/2001/XMLSchema.xsd"

def validate(modelDocument, schemaElement, targetNamespace):
    modelXbrl = modelDocument.modelXbrl 
    modelManager = modelXbrl.modelManager
    """
    if not hasattr(modelManager, "xmlSchemaSchema"):
        if getattr(modelManager, "modelXmlSchemaIsLoading", False):
            return
        modelManager.modelXmlSchemaIsLoading = True
        '''
        priorValidateDisclosureSystem = modelManager.validateDisclosureSystem
        modelManager.validateDisclosureSystem = False
        modelManager.xmlSchemaSchema = ModelXbrl.load(modelManager, XMLSchemaURI, _("validate schema"))
        modelManager.validateDisclosureSystem = priorValidateDisclosureSystem
        '''
        startedAt = time.time()
        filePath = modelManager.cntlr.webCache.getfilename(XMLSchemaURI)
        modelManager.showStatus(_("lxml compiling XML Schema for Schemas"))
        modelManager.xmlSchemaSchema = etree.XMLSchema(file=filePath)
        modelXbrl.info("info:xmlSchemaValidator", format_string(modelXbrl.modelManager.locale, 
                                            _("schema for XML schemas loaded into lxml %.3f secs"), 
                                            time.time() - startedAt),
                                            modelDocument=XMLSchemaURI)
        modelManager.showStatus("")
        del modelManager.modelXmlSchemaIsLoading
    #XmlValidate.validate(modelManager.xmlSchemaSchema, schemaElement)
    #startedAt = time.time()
    validationSuccess = modelManager.xmlSchemaSchema.validate(schemaElement)
    #modelXbrl.info("info:xmlSchemaValidator", format_string(modelXbrl.modelManager.locale, 
    #                                    _("schema validated in %.3f secs"), 
    #                                    time.time() - startedAt),
    #                                    modelDocument=modelDocument)
    if not validationSuccess:
        for error in modelManager.xmlSchemaSchema.error_log:
            modelXbrl.error("xmlSchema:syntax",
                    _("%(error)s, %(fileName)s, line %(line)s, column %(column)s, %(sourceAction)s source element"),
                    modelObject=modelDocument, fileName=modelDocument.basename, 
                    error=error.message, line=error.line, column=error.column, sourceAction=("xml schema"))
        modelManager.xmlSchemaSchema._clear_error_log()
    """

    declaredNamespaces = set(doc.targetNamespace
                             for doc, docRef in modelDocument.referencesDocument.items()
                             if docRef.referenceType in ("include", "import"))
    if targetNamespace:
        declaredNamespaces.add(targetNamespace)
    
    # check schema semantics
    def resolvedQnames(elt, qnDefs):
        for attrName, attrType, mdlObjects in qnDefs:
            attr = elt.get(attrName)
            if attr is not None:
                try:
                    qnValue = qname(elt, attr, castException=ValueError, prefixException=ValueError)
                    if qnValue.namespaceURI == XbrlConst.xsd:
                        if attrType != ModelType:
                            raise ValueError("{0} can not have xml schema namespace")
                        if qnValue.localName not in {
                                "anySimpleType", "anyType",
                                "string", "boolean", "float", "double", "decimal", "duration", "dateTime", "time", "date", 
                                "gYearMonth", "gYear", "gMonthDay", "gDay", "gMonth", 
                                "hexBinary", "base64Binary", 
                                "anyURI", "QName", "NOTATION", 
                                "normalizedString", "token", "language", 
                                "IDREFS", "ENTITIES", "NMTOKEN", "NMTOKENS", "NCName", 
                                "ID", "IDREF", 
                                "integer", "nonPositiveInteger", "negativeInteger", 
                                "long", "int", "short", "byte", 
                                "nonNegativeInteger", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", 
                                "positiveInteger"
                                }:
                            raise ValueError("{0} qname {1} not recognized".format(attrName, attr))
                    # qname must be defined in an imported or included schema
                    elif qnValue.namespaceURI not in declaredNamespaces:
                        raise ValueError("Namespace is not defined by an import or include element")
                    elif qnValue not in mdlObjects:
                        raise ValueError("{0} is not defined".format(attrName))
                    elif not isinstance(mdlObjects[qnValue], attrType):
                        raise ValueError("{0} not resolved to expected object type".format(attrName))
                except ValueError as err:
                    modelXbrl.error("xmlSchema:valueError",
                        _("Element attribute %(typeName)s value error: %(value)s, %(error)s"),
                        modelObject=elt,
                        typeName=attrName,
                        value=attr,
                        error=err)
                    
    def checkSchemaElements(parentElement):
        for elt in parentElement.iterchildren():
            if isinstance(elt,ModelObject) and elt.namespaceURI == XbrlConst.xsd:
                ln = elt.localName
                if ln == "element":
                    resolvedQnames(elt, (("ref", ModelConcept, modelXbrl.qnameConcepts),
                                         ("substitutionGroup", ModelConcept, modelXbrl.qnameConcepts),
                                         ("type", ModelType, modelXbrl.qnameTypes)))
                elif ln == "attribute":
                    resolvedQnames(elt, (("ref", ModelAttribute, modelXbrl.qnameAttributes),
                                         ("type", ModelType, modelXbrl.qnameTypes)))
            checkSchemaElements(elt)

    checkSchemaElements(schemaElement)
    
