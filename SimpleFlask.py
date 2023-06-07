from flask import Flask, request, send_file
from flask import render_template
from xml.dom import minidom
import pandas as pd
from werkzeug.utils import secure_filename
import csv


app = Flask(__name__, template_folder='templates')

@app.route('/')
@app.route('/hello')
def hello():
    # Render the page
    return render_template('index.html')

@app.route('/convert', methods=("POST", "GET"))
def convert():
    myfile = request.files['myfile1']
    myfile.save(myfile.filename)
    p_name = request.form['project_name']
    schema_name = request.form['schema_name']
    converted_file = convert_file(myfile.filename,p_name,schema_name)
    return send_file(converted_file, as_attachment=True)
    #return "Hello there!"



def convert_file(file_name, project_name, schema_name):
    xsd_root = minidom.Document()
    if project_name == "":
        project_name = "Project_Name"
    if schema_name == "":
        schema_name = "Schema_Name"

    xsd_schema_root = xsd_root.createElement('xsd:schema')
    xsd_schema_root.setAttribute("xmlns", "http://www.seeburger.com/" + project_name + "/" + schema_name)
    xsd_schema_root.setAttribute("xmlns:bic", "http://www.seeburger.com/bicng/lang/schema/")
    xsd_schema_root.setAttribute("xmlns:inhouse", "http://www.seeburger.com/bicng/lang/schema/inhouse")
    xsd_schema_root.setAttribute("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    xsd_schema_root.setAttribute("bic:messageType", "INHOUSE")
    xsd_schema_root.setAttribute("elementFormDefault", "qualified")
    xsd_schema_root.setAttribute("targetNamespace", "http://www.seeburger.com/" + project_name + "/" + schema_name)

    xsd_root.appendChild(xsd_schema_root)

    xsd_import_element = xsd_root.createElement('xsd:import')
    xsd_import_element.setAttribute("namespace", "http://www.seeburger.com/bicng/lang/schema/inhouse")
    xsd_import_element.setAttribute("schemaLocation", "platform:/plugin/com.seeburger.bicng.lang.schema.facade.inhouse"
                                                      "/resources/inhouse.xsd")

    xsd_schema_root.appendChild(xsd_import_element)
    xsd_schema_header = xsd_root.createElement('xsd:element')
    xsd_schema_header.setAttribute('name', schema_name)
    xsd_schema_root.appendChild(xsd_schema_header)

    header_ComplexType = xsd_root.createElement('xsd:complexType')
    xsd_schema_header.appendChild(header_ComplexType)

    header_ComplexContent = xsd_root.createElement('xsd:complexContent')
    header_ComplexType.appendChild(header_ComplexContent)

    header_extension = xsd_root.createElement('xsd:extension')
    header_ComplexContent.appendChild(header_extension)
    header_extension.setAttribute('base', 'inhouse:InhouseMessageRoot')

    header_sequence = xsd_root.createElement('xsd:sequence')
    header_extension.appendChild(header_sequence)
    xsd_loop_start_sequence = ''
    with open(file_name, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            min_occur = row['min occ']
            max_occur = row['max occ']

            if max_occur == '*' or max_occur == '':
                max_occur = 'unbounded'
            if min_occur == '':
                min_occur = '0'

            if row['Type'] == 'LS':
                xsd_loop_start = xsd_root.createElement('xsd:element')
                if xsd_loop_start_sequence == '':
                    header_sequence.appendChild(xsd_loop_start)
                else:
                    xsd_loop_start_sequence.appendChild(xsd_loop_start)
                xsd_loop_start.setAttribute('maxOccurs', max_occur)
                xsd_loop_start.setAttribute('minOccurs', min_occur)
                xsd_loop_start.setAttribute('name', row['Loop/Rec Name'])
                ComplexType = xsd_root.createElement('xsd:complexType')
                xsd_loop_start.appendChild(ComplexType)
                ComplexContent = xsd_root.createElement('xsd:complexContent')
                ComplexType.appendChild(ComplexContent)
                extension = xsd_root.createElement('xsd:extension')
                extension.setAttribute('base', "inhouse:InhouseSegmentGroup")
                ComplexContent.appendChild(extension)
                xsd_loop_start_sequence = xsd_root.createElement('xsd:sequence')
                extension.appendChild(xsd_loop_start_sequence)
            if row['Type'] == 'LE':
                xsd_loop_start = ''
            if row['Type'] == 'RC':
                xsd_record_segment = xsd_root.createElement('xsd:element')
                if xsd_loop_start_sequence == '':
                    header_sequence.appendChild(xsd_record_segment)
                else:
                    xsd_loop_start_sequence.appendChild(xsd_record_segment)
                xsd_record_segment.setAttribute('maxOccurs', max_occur)
                xsd_record_segment.setAttribute('minOccurs', min_occur)
                xsd_record_segment.setAttribute('name', row['Loop/Rec Name'])
                ComplexType = xsd_root.createElement('xsd:complexType')
                xsd_record_segment.appendChild(ComplexType)
                ComplexContent = xsd_root.createElement('xsd:complexContent')
                ComplexType.appendChild(ComplexContent)
                extension = xsd_root.createElement('xsd:extension')
                extension.setAttribute('base', "inhouse:Segment")
                ComplexContent.appendChild(extension)
                sequence = xsd_root.createElement('xsd:sequence')
                extension.appendChild(sequence)
            elif row['Type'] != 'RC' and row['Type'] != 'LS' and row['Type'] != '' and row['Type'] != 'LE':
                default_value = row['Default Value']
                field = xsd_root.createElement('xsd:element')
                if default_value != '':
                    field.setAttribute('default', default_value)
                field.setAttribute('maxOccurs', max_occur)
                field.setAttribute('minOccurs', min_occur)
                field.setAttribute('name', row['Field Name'])
                sequence.appendChild(field)
                field_type = xsd_root.createElement('xsd:simpleType')
                field.appendChild(field_type)
                restr = xsd_root.createElement('xsd:restriction')
                field_type.appendChild(restr)
                restr.setAttribute('base', "inhouse:AN")
                fieldlength = xsd_root.createElement('xsd:length')
                restr.appendChild(fieldlength)
                fieldlength.setAttribute('value', row['Length'].split('.')[0])
            line_count = line_count + 1

    xml_str = xsd_root.toprettyxml(indent="\t")

    save_path_file = 'schema_test.xml'

    with open(save_path_file, "w") as f:
        f.write(xml_str)
    return save_path_file

if __name__ == '__main__':
    # Run the app server on localhost:4449
    app.run(debug=True)