{{/*
Expand the name of the chart.
*/}}
{{- define "oil-pipeline.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncated to 63 chars because Kubernetes DNS names have that limit.
*/}}
{{- define "oil-pipeline.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-oil-pipeline" .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Chart label — used to track which chart version is deployed.
*/}}
{{- define "oil-pipeline.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to every resource.
*/}}
{{- define "oil-pipeline.labels" -}}
helm.sh/chart: {{ include "oil-pipeline.chart" . }}
app.kubernetes.io/name: {{ include "oil-pipeline.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: oil-pipeline
{{- end }}

{{/*
Selector labels — used in matchLabels and Service selectors.
Must be a stable, minimal subset of the common labels.
*/}}
{{- define "oil-pipeline.selectorLabels" -}}
app.kubernetes.io/name: {{ include "oil-pipeline.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Return the fully-qualified name of the PostgreSQL service.
All other services reference PostgreSQL by this name.
*/}}
{{- define "oil-pipeline.postgresHost" -}}
{{- printf "%s-postgres" (include "oil-pipeline.fullname" .) }}
{{- end }}
