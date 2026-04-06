import React, { useState, useEffect } from 'react';
import './ReportingDashboard.css';

interface ReportTemplate {
  id: string;
  name: string;
  template_type: string;
  primary_color: string;
  secondary_color: string;
  company_name?: string;
  is_default: boolean;
  created_at: string;
}

interface FilingReminder {
  id: string;
  filing_type: string;
  title: string;
  deadline: string;
  jurisdiction: string;
  status: string;
}

interface KycRecord {
  id: string;
  client_name: string;
  risk_tolerance: string;
  kyc_status: string;
  suitability_score: number;
  created_at: string;
}

interface ComplianceDocument {
  id: string;
  document_type: string;
  title: string;
  status: string;
  filing_date?: string;
  period_covered?: string;
}

const ReportingDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'reports' | 'kyc' | 'compliance' | 'reminders'>('reports');
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [reminders, setReminders] = useState<FilingReminder[]>([]);
  const [kycRecords, setKycRecords] = useState<KycRecord[]>([]);
  const [documents, setDocuments] = useState<ComplianceDocument[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Report generation state
  const [reportType, setReportType] = useState('quarterly');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [includeGips, setIncludeGips] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const endpoints: Record<string, string> = {
        reports: '/api/v1/reporting/templates',
        kyc: '/api/v1/reporting/kyc',
        compliance: '/api/v1/reporting/documents',
        reminders: '/api/v1/reporting/reminders/upcoming',
      };

      const response = await fetch(endpoints[activeTab], {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        switch (activeTab) {
          case 'reports':
            setTemplates(data);
            break;
          case 'kyc':
            setKycRecords(data);
            break;
          case 'compliance':
            setDocuments(data);
            break;
          case 'reminders':
            setReminders(data);
            break;
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/reporting/generate/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          report_type: reportType,
          period_start: periodStart,
          period_end: periodEnd,
          include_holdings: true,
          include_performance: true,
          include_allocation: true,
          include_risk_metrics: true,
          include_gips_disclosure: includeGips,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Report generated! ID: ${data.report_id}`);
      }
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
      case 'completed':
        return 'status-success';
      case 'pending':
        return 'status-warning';
      case 'rejected':
        return 'status-danger';
      default:
        return '';
    }
  };

  return (
    <div className="reporting-dashboard">
      <div className="dashboard-header">
        <h1>Institutional Reporting & Compliance</h1>
        <p>Professional-grade reports, KYC management, and regulatory compliance</p>
      </div>

      <div className="dashboard-tabs">
        <button
          className={activeTab === 'reports' ? 'active' : ''}
          onClick={() => setActiveTab('reports')}
        >
          📊 Report Generation
        </button>
        <button
          className={activeTab === 'kyc' ? 'active' : ''}
          onClick={() => setActiveTab('kyc')}
        >
          👤 KYC Records
        </button>
        <button
          className={activeTab === 'compliance' ? 'active' : ''}
          onClick={() => setActiveTab('compliance')}
        >
          📄 Compliance Documents
        </button>
        <button
          className={activeTab === 'reminders' ? 'active' : ''}
          onClick={() => setActiveTab('reminders')}
        >
          ⏰ Filing Reminders
        </button>
      </div>

      <div className="dashboard-content">
        {loading ? (
          <div className="loading-spinner">Loading...</div>
        ) : (
          <>
            {activeTab === 'reports' && (
              <div className="reports-section">
                <div className="report-generator">
                  <h2>Generate Professional Report</h2>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Report Type</label>
                      <select
                        value={reportType}
                        onChange={(e) => setReportType(e.target.value)}
                      >
                        <option value="monthly">Monthly Report</option>
                        <option value="quarterly">Quarterly Review</option>
                        <option value="annual">Annual Summary</option>
                        <option value="gips">GIPS Compliance Report</option>
                        <option value="custom">Custom Report</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Period Start</label>
                      <input
                        type="date"
                        value={periodStart}
                        onChange={(e) => setPeriodStart(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label>Period End</label>
                      <input
                        type="date"
                        value={periodEnd}
                        onChange={(e) => setPeriodEnd(e.target.value)}
                      />
                    </div>
                    <div className="form-group checkbox">
                      <label>
                        <input
                          type="checkbox"
                          checked={includeGips}
                          onChange={(e) => setIncludeGips(e.target.checked)}
                        />
                        Include GIPS Disclosure
                      </label>
                    </div>
                  </div>
                  <div className="button-group">
                    <button className="btn-primary" onClick={generateReport}>
                      Generate PDF Report
                    </button>
                    <button className="btn-secondary">
                      Generate Excel Report
                    </button>
                  </div>
                </div>

                <div className="templates-section">
                  <h3>Report Templates</h3>
                  <div className="templates-grid">
                    {templates.length === 0 ? (
                      <p className="no-data">No templates yet. Create your first template.</p>
                    ) : (
                      templates.map((template) => (
                        <div key={template.id} className="template-card">
                          <div
                            className="template-preview"
                            style={{
                              background: `linear-gradient(135deg, ${template.primary_color}, ${template.secondary_color})`,
                            }}
                          >
                            <span>Preview</span>
                          </div>
                          <div className="template-info">
                            <h4>{template.name}</h4>
                            <span className="template-type">{template.template_type}</span>
                            {template.is_default && (
                              <span className="default-badge">Default</span>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'kyc' && (
              <div className="kyc-section">
                <div className="section-header">
                  <h2>Client KYC Records</h2>
                  <button className="btn-primary">+ Add Client</button>
                </div>
                <div className="kyc-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Client Name</th>
                        <th>Risk Tolerance</th>
                        <th>Suitability Score</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kycRecords.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="no-data">
                            No KYC records yet
                          </td>
                        </tr>
                      ) : (
                        kycRecords.map((record) => (
                          <tr key={record.id}>
                            <td>{record.client_name}</td>
                            <td>{record.risk_tolerance}</td>
                            <td>{record.suitability_score.toFixed(0)}%</td>
                            <td>
                              <span className={`status-badge ${getStatusColor(record.kyc_status)}`}>
                                {record.kyc_status}
                              </span>
                            </td>
                            <td>{new Date(record.created_at).toLocaleDateString()}</td>
                            <td>
                              <button className="btn-small">View</button>
                              <button className="btn-small">Upload Docs</button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'compliance' && (
              <div className="compliance-section">
                <div className="section-header">
                  <h2>Regulatory Documents</h2>
                  <button className="btn-primary">+ New Document</button>
                </div>
                <div className="compliance-grid">
                  {documents.length === 0 ? (
                    <p className="no-data">No compliance documents yet</p>
                  ) : (
                    documents.map((doc) => (
                      <div key={doc.id} className="compliance-card">
                        <div className="doc-icon">
                          {doc.document_type.toUpperCase()}
                        </div>
                        <div className="doc-info">
                          <h4>{doc.title}</h4>
                          <p>{doc.period_covered || 'N/A'}</p>
                          <span className={`status-badge ${getStatusColor(doc.status)}`}>
                            {doc.status}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'reminders' && (
              <div className="reminders-section">
                <div className="section-header">
                  <h2>Upcoming Filing Deadlines</h2>
                  <button className="btn-primary">+ Add Reminder</button>
                </div>
                <div className="reminders-list">
                  {reminders.length === 0 ? (
                    <p className="no-data">No upcoming reminders</p>
                  ) : (
                    reminders.map((reminder) => (
                      <div key={reminder.id} className="reminder-card">
                        <div className="reminder-date">
                          <span className="day">
                            {new Date(reminder.deadline).getDate()}
                          </span>
                          <span className="month">
                            {new Date(reminder.deadline).toLocaleString('default', { month: 'short' })}
                          </span>
                        </div>
                        <div className="reminder-info">
                          <h4>{reminder.title}</h4>
                          <span className="jurisdiction">{reminder.jurisdiction}</span>
                          <span className={`status-badge ${getStatusColor(reminder.status)}`}>
                            {reminder.status}
                          </span>
                        </div>
                        <div className="reminder-actions">
                          <button className="btn-small">Mark Complete</button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ReportingDashboard;
