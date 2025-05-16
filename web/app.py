from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from datetime import datetime
import sys
import os
import json
import pandas as pd
import io
sys.path.append('../etl')
from setup_ecrf import (
    get_db_connection,
    create_form_instance,
    save_form_response,
    get_form_data
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    """Home page showing available forms"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all active forms
        cursor.execute("""
            SELECT FormID, FormName, FormVersion, FormDescription
            FROM dbo.ECRFForms
            WHERE IsActive = 1
            ORDER BY FormName
        """)
        
        forms = cursor.fetchall()
        return render_template('index.html', forms=forms)
        
    except Exception as e:
        flash(f"Error loading forms: {str(e)}", "error")
        return render_template('index.html', forms=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/form/<int:form_id>')
def view_form(form_id):
    """View form structure and fields"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get form details
        cursor.execute("""
            SELECT FormName, FormVersion, FormDescription
            FROM dbo.ECRFForms
            WHERE FormID = ?
        """, form_id)
        
        form = cursor.fetchone()
        
        # Get sections and fields
        cursor.execute("""
            SELECT 
                s.SectionID,
                s.SectionName,
                s.SectionDescription,
                fi.FieldID,
                fi.FieldName,
                fi.FieldLabel,
                fi.FieldType,
                fi.IsRequired,
                fi.ValidationRules,
                fi.FieldOrder
            FROM dbo.ECRFSections s
            JOIN dbo.ECRFFields fi ON s.SectionID = fi.SectionID
            WHERE s.FormID = ?
            ORDER BY s.SectionOrder, fi.FieldOrder
        """, form_id)
        
        sections = {}
        for row in cursor.fetchall():
            section_id = row[0]
            if section_id not in sections:
                sections[section_id] = {
                    'name': row[1],
                    'description': row[2],
                    'fields': []
                }
            sections[section_id]['fields'].append({
                'id': row[3],
                'name': row[4],
                'label': row[5],
                'type': row[6],
                'required': row[7],
                'validation': row[8],
                'order': row[9]
            })
        
        return render_template('form.html', 
                             form=form,
                             sections=sections,
                             form_id=form_id)
        
    except Exception as e:
        flash(f"Error loading form: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/patient/<int:patient_id>/form/<int:form_id>/new', methods=['GET', 'POST'])
def new_form_instance(patient_id, form_id):
    """Create a new form instance for a patient"""
    if request.method == 'POST':
        try:
            # Create new form instance
            instance_id = create_form_instance(
                patient_id=patient_id,
                form_id=form_id,
                visit_date=datetime.now(),
                created_by=request.form.get('created_by', 'Unknown')
            )
            
            # Save responses
            for field_id, value in request.form.items():
                if field_id.startswith('field_'):
                    field_id = int(field_id.split('_')[1])
                    save_form_response(
                        instance_id=instance_id,
                        field_id=field_id,
                        response_value=value,
                        modified_by=request.form.get('created_by', 'Unknown')
                    )
            
            flash("Form submitted successfully!", "success")
            return redirect(url_for('view_form_instance', instance_id=instance_id))
            
        except Exception as e:
            flash(f"Error submitting form: {str(e)}", "error")
            return redirect(url_for('view_form', form_id=form_id))
    
    # GET request - show form
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get patient info
        cursor.execute("""
            SELECT FirstName, LastName
            FROM dbo.Patients
            WHERE PatientID = ?
        """, patient_id)
        
        patient = cursor.fetchone()
        
        # Get form structure
        cursor.execute("""
            SELECT 
                s.SectionID,
                s.SectionName,
                s.SectionDescription,
                fi.FieldID,
                fi.FieldName,
                fi.FieldLabel,
                fi.FieldType,
                fi.IsRequired,
                fi.ValidationRules,
                fi.FieldOrder
            FROM dbo.ECRFSections s
            JOIN dbo.ECRFFields fi ON s.SectionID = fi.SectionID
            WHERE s.FormID = ?
            ORDER BY s.SectionOrder, fi.FieldOrder
        """, form_id)
        
        sections = {}
        for row in cursor.fetchall():
            section_id = row[0]
            if section_id not in sections:
                sections[section_id] = {
                    'name': row[1],
                    'description': row[2],
                    'fields': []
                }
            sections[section_id]['fields'].append({
                'id': row[3],
                'name': row[4],
                'label': row[5],
                'type': row[6],
                'required': row[7],
                'validation': row[8],
                'order': row[9]
            })
        
        return render_template('new_form.html',
                             patient=patient,
                             form_id=form_id,
                             sections=sections)
        
    except Exception as e:
        flash(f"Error loading form: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/instance/<int:instance_id>')
def view_form_instance(instance_id):
    """View a specific form instance"""
    try:
        form_data = get_form_data(instance_id)
        
        # Organize data by sections
        sections = {}
        for row in form_data:
            form_name, section_name, field_name, field_label, field_type, \
            response_value, response_date, modified_date, modified_by = row
            
            if section_name not in sections:
                sections[section_name] = []
            
            sections[section_name].append({
                'label': field_label,
                'value': response_value,
                'type': field_type,
                'date': response_date,
                'modified_by': modified_by
            })
        
        return render_template('view_instance.html',
                             form_name=form_data[0][0] if form_data else 'Unknown Form',
                             sections=sections)
        
    except Exception as e:
        flash(f"Error loading form instance: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/form/<int:form_id>/data')
def form_data(form_id):
    """View and export form data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get form details
        cursor.execute("""
            SELECT FormName, FormVersion
            FROM dbo.ECRFForms
            WHERE FormID = ?
        """, form_id)
        form = cursor.fetchone()
        
        # Get all instances of this form
        cursor.execute("""
            SELECT 
                i.InstanceID,
                p.PatientID,
                p.FirstName,
                p.LastName,
                i.VisitDate,
                i.Status,
                i.CreatedBy,
                i.CreatedDate
            FROM dbo.ECRFFormInstances i
            JOIN dbo.Patients p ON i.PatientID = p.PatientID
            WHERE i.FormID = ?
            ORDER BY i.VisitDate DESC
        """, form_id)
        instances = cursor.fetchall()
        
        return render_template('form_data.html',
                             form=form,
                             form_id=form_id,
                             instances=instances)
        
    except Exception as e:
        flash(f"Error loading form data: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/form/<int:form_id>/export')
def export_form_data(form_id):
    """Export form data to CSV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get form details
        cursor.execute("""
            SELECT FormName
            FROM dbo.ECRFForms
            WHERE FormID = ?
        """, form_id)
        form_name = cursor.fetchone()[0]
        
        # Get all responses for this form
        cursor.execute("""
            SELECT 
                p.PatientID,
                p.FirstName,
                p.LastName,
                i.VisitDate,
                s.SectionName,
                f.FieldLabel,
                r.ResponseValue,
                r.ResponseDate,
                r.ModifiedBy,
                r.ModifiedDate
            FROM dbo.ECRFFormInstances i
            JOIN dbo.Patients p ON i.PatientID = p.PatientID
            JOIN dbo.ECRFResponses r ON i.InstanceID = r.InstanceID
            JOIN dbo.ECRFFields f ON r.FieldID = f.FieldID
            JOIN dbo.ECRFSections s ON f.SectionID = s.SectionID
            WHERE i.FormID = ?
            ORDER BY i.VisitDate DESC, p.PatientID, s.SectionOrder, f.FieldOrder
        """, form_id)
        
        # Convert to DataFrame
        columns = ['PatientID', 'FirstName', 'LastName', 'VisitDate', 'Section', 
                  'Field', 'Value', 'ResponseDate', 'ModifiedBy', 'ModifiedDate']
        df = pd.DataFrame(cursor.fetchall(), columns=columns)
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Generate filename
        filename = f"{form_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f"Error exporting form data: {str(e)}", "error")
        return redirect(url_for('form_data', form_id=form_id))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/form/<int:form_id>/visualize')
def visualize_form_data(form_id):
    """Visualize form data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get form details
        cursor.execute("""
            SELECT FormName
            FROM dbo.ECRFForms
            WHERE FormID = ?
        """, form_id)
        form_name = cursor.fetchone()[0]
        
        # Get all patients who have data for this form
        cursor.execute("""
            SELECT DISTINCT 
                p.PatientID,
                p.FirstName + ' ' + p.LastName as PatientName,
                p.LastName,
                p.FirstName
            FROM dbo.Patients p
            JOIN dbo.ECRFFormInstances i ON p.PatientID = i.PatientID
            WHERE i.FormID = ?
            ORDER BY p.LastName, p.FirstName
        """, form_id)
        patients = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        # Get numeric fields for visualization
        cursor.execute("""
            SELECT 
                f.FieldID,
                f.FieldLabel,
                s.SectionName,
                f.ValidationRules
            FROM dbo.ECRFFields f
            JOIN dbo.ECRFSections s ON f.SectionID = s.SectionID
            WHERE s.FormID = ? AND f.FieldType = 'number'
        """, form_id)
        numeric_fields = cursor.fetchall()
        
        # Get data for each numeric field
        field_data = {}
        for field in numeric_fields:
            field_id = field[0]
            cursor.execute("""
                SELECT 
                    i.VisitDate,
                    r.ResponseValue,
                    p.PatientID,
                    p.FirstName + ' ' + p.LastName as PatientName
                FROM dbo.ECRFResponses r
                JOIN dbo.ECRFFormInstances i ON r.InstanceID = i.InstanceID
                JOIN dbo.Patients p ON i.PatientID = p.PatientID
                WHERE r.FieldID = ? AND i.FormID = ?
                ORDER BY i.VisitDate
            """, field_id, form_id)
            field_data[field[0]] = {
                'label': field[1],
                'section': field[2],
                'validation': json.loads(field[3]) if field[3] else {},
                'data': cursor.fetchall()
            }
        
        return render_template('form_visualization.html',
                             form_name=form_name,
                             form_id=form_id,
                             field_data=field_data,
                             patients=patients)
        
    except Exception as e:
        flash(f"Error loading visualization data: {str(e)}", "error")
        return redirect(url_for('form_data', form_id=form_id))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/form/<int:form_id>/compare', methods=['GET', 'POST'])
def compare_patients(form_id):
    """Compare patient data and generate statistical analysis"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get form details
        cursor.execute("""
            SELECT FormName
            FROM dbo.ECRFForms
            WHERE FormID = ?
        """, form_id)
        form_name = cursor.fetchone()[0]
        
        if request.method == 'POST':
            patient_ids = request.form.getlist('patient_ids')
            date_range = request.form.get('date_range', 'all')
            
            # Get numeric fields for comparison
            cursor.execute("""
                SELECT 
                    f.FieldID,
                    f.FieldLabel,
                    s.SectionName,
                    f.ValidationRules
                FROM dbo.ECRFFields f
                JOIN dbo.ECRFSections s ON f.SectionID = s.SectionID
                WHERE s.FormID = ? AND f.FieldType = 'number'
            """, form_id)
            numeric_fields = cursor.fetchall()
            
            # Get data for each field and patient
            comparison_data = {}
            for field in numeric_fields:
                field_id = field[0]
                field_data = []
                
                for patient_id in patient_ids:
                    cursor.execute("""
                        SELECT 
                            i.VisitDate,
                            r.ResponseValue,
                            p.PatientID,
                            p.FirstName + ' ' + p.LastName as PatientName
                        FROM dbo.ECRFResponses r
                        JOIN dbo.ECRFFormInstances i ON r.InstanceID = i.InstanceID
                        JOIN dbo.Patients p ON i.PatientID = p.PatientID
                        WHERE r.FieldID = ? 
                        AND i.FormID = ?
                        AND p.PatientID = ?
                        ORDER BY i.VisitDate
                    """, field_id, form_id, patient_id)
                    
                    patient_data = cursor.fetchall()
                    if patient_data:
                        field_data.append({
                            'patient_id': patient_id,
                            'patient_name': patient_data[0][3],
                            'data': patient_data
                        })
                
                if field_data:
                    comparison_data[field[0]] = {
                        'label': field[1],
                        'section': field[2],
                        'validation': json.loads(field[3]) if field[3] else {},
                        'patient_data': field_data
                    }
            
            return render_template('patient_comparison.html',
                                 form_name=form_name,
                                 form_id=form_id,
                                 comparison_data=comparison_data,
                                 date_range=date_range)
        
        # GET request - show patient selection form
        cursor.execute("""
            SELECT DISTINCT 
                p.PatientID,
                p.FirstName + ' ' + p.LastName as PatientName
            FROM dbo.Patients p
            JOIN dbo.ECRFFormInstances i ON p.PatientID = i.PatientID
            WHERE i.FormID = ?
            ORDER BY p.LastName, p.FirstName
        """, form_id)
        patients = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        return render_template('select_patients.html',
                             form_name=form_name,
                             form_id=form_id,
                             patients=patients)
        
    except Exception as e:
        flash(f"Error comparing patient data: {str(e)}", "error")
        return redirect(url_for('form_data', form_id=form_id))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True) 