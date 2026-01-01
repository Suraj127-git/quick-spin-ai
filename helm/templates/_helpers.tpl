{{/*
Expand the name of the chart.
*/}}
{{- define "quickspin-ai.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "quickspin-ai.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "quickspin-ai.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "quickspin-ai.labels" -}}
helm.sh/chart: {{ include "quickspin-ai.chart" . }}
{{ include "quickspin-ai.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: quickspin
app.kubernetes.io/component: ai-service
{{- end }}

{{/*
Selector labels
*/}}
{{- define "quickspin-ai.selectorLabels" -}}
app.kubernetes.io/name: {{ include "quickspin-ai.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: {{ .Values.deployment.name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "quickspin-ai.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default .Values.serviceAccount.name .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the image pull secrets
*/}}
{{- define "quickspin-ai.imagePullSecrets" -}}
{{- if .Values.imagePullSecrets }}
imagePullSecrets:
{{- range .Values.imagePullSecrets }}
  - name: {{ .name }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Get the image name
*/}}
{{- define "quickspin-ai.image" -}}
{{- $tag := .Values.deployment.image.tag | default .Values.image.tag | default .Chart.AppVersion -}}
{{- printf "%s:%s" .Values.deployment.image.repository $tag }}
{{- end }}

{{/*
Create Secrets name
*/}}
{{- define "quickspin-ai.secretsName" -}}
{{- default "quickspin-ai-secrets" .Values.secrets.name }}
{{- end }}

{{/*
Create PVC name
*/}}
{{- define "quickspin-ai.pvcName" -}}
{{- default "quickspin-ai-chroma-pvc" .Values.persistence.name }}
{{- end }}

{{/*
Return the appropriate apiVersion for HPA
*/}}
{{- define "quickspin-ai.hpa.apiVersion" -}}
{{- if .Capabilities.APIVersions.Has "autoscaling/v2" -}}
{{- print "autoscaling/v2" -}}
{{- else -}}
{{- print "autoscaling/v2beta2" -}}
{{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for Ingress
*/}}
{{- define "quickspin-ai.ingress.apiVersion" -}}
{{- if .Capabilities.APIVersions.Has "networking.k8s.io/v1" -}}
{{- print "networking.k8s.io/v1" -}}
{{- else if .Capabilities.APIVersions.Has "networking.k8s.io/v1beta1" -}}
{{- print "networking.k8s.io/v1beta1" -}}
{{- else -}}
{{- print "extensions/v1beta1" -}}
{{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for PodDisruptionBudget
*/}}
{{- define "quickspin-ai.pdb.apiVersion" -}}
{{- if .Capabilities.APIVersions.Has "policy/v1" -}}
{{- print "policy/v1" -}}
{{- else -}}
{{- print "policy/v1beta1" -}}
{{- end -}}
{{- end -}}

{{/*
Environment variables from Secrets
*/}}
{{- define "quickspin-ai.envFromSecrets" -}}
{{- range .Values.envFromSecrets }}
- name: {{ .name }}
  valueFrom:
    secretKeyRef:
      name: {{ include "quickspin-ai.secretsName" $ }}
      key: {{ .key }}
{{- end }}
{{- end }}
