#!/bin/bash

# This script creates a new Ollama model named 'gpt-oss-l' based on 'gpt-oss',
# with a much larger context window AND a custom template to ensure
# compatibility with cline's tool-calling format.

# --- Configuration ---
BASE_MODEL="gpt-oss:latest"
NEW_MODEL_NAME="gpt-oss-l"
CONTEXT_WINDOW=65536 # 64k tokens

# A specific, instruction-focused system prompt to improve tool-calling compliance.
read -r -d '' SYSTEM_PROMPT <<'EOF'
You are a highly specialized AI agent. Your primary function is to analyze requests and respond by calling the appropriate tool. You must strictly adhere to the provided tool definitions and output formats.

**Core Directives:**
1.  **Analyze the Goal:** Understand the user's ultimate objective.
2.  **Select a Tool:** Choose the single best tool to make progress towards that goal.
3.  **Format the Call:** Your response MUST be a tool call. Adhere strictly to the required channel (`analysis`) and JSON format for the arguments.
4.  **No Conversation:** Do not provide conversational text, apologies, or explanations. Your only output is a tool call.
EOF

echo "--- Preparing to create large-context, cline-compatible model: '$NEW_MODEL_NAME' ---"

# --- Create the Modelfile ---
# This Modelfile has been corrected for syntax and logic errors.
cat > Modelfile_large <<EOF
# Modelfile for a large-context, cline-compatible version of $BASE_MODEL
FROM $BASE_MODEL
SYSTEM """$SYSTEM_PROMPT"""
TEMPLATE """<|start|>system<|message|>
# FIX #1: Removed the hardcoded "You are ChatGPT" identity.
# The SYSTEM prompt from the script will be used instead via the 'developer' message block.
Knowledge cutoff: 2024-06
Current date: {{ currentDate }}
{{- if and .IsThinkSet .Think (ne .ThinkLevel "") }}

Reasoning: {{ .ThinkLevel }}
{{- else if or (not .IsThinkSet) (and .IsThinkSet .Think) }}

Reasoning: high
{{- end }}

{{- \$hasNonBuiltinTools := false }}
{{- if .Tools -}}
{{- \$hasBrowserSearch := false }}
{{- \$hasBrowserOpen := false }}
{{- \$hasBrowserFind := false }}
{{- \$hasPython := false }}
  {{- range .Tools }}
    {{- if eq .Function.Name "browser.search" -}}{{- \$hasBrowserSearch = true -}}
    {{- else if eq .Function.Name "browser.open" -}}{{- \$hasBrowserOpen = true -}}
    {{- else if eq .Function.Name "browser.find" -}}{{- \$hasBrowserFind = true -}}
    {{- else if eq .Function.Name "python" -}}{{- \$hasPython = true -}}
    {{- else }}{{ \$hasNonBuiltinTools = true -}}
    {{- end }}
  {{- end }}
{{- if or \$hasBrowserSearch \$hasBrowserOpen \$hasBrowserFind \$hasPython }}

# Tools
{{- if or \$hasBrowserSearch \$hasBrowserOpen \$hasBrowserFind }}

## browser
namespace browser {
{{- if \$hasBrowserSearch }}
type search = (_: {
query: string,
topn?: number,
source?: string,
}) => any;
{{- end }}
{{- if \$hasBrowserOpen }}
type open = (_: {
id?: number | string,
cursor?: number,
loc?: number,
num_lines?: number,
view_source?: boolean,
source?: string,
}) => any;
{{- end }}
{{- if \$hasBrowserFind }}
type find = (_: {
pattern: string,
cursor?: number,
}) => any;
{{- end }}
} // namespace browser
{{- end }}
{{- if \$hasPython }}

## python
{{- end }}
{{- end }}
{{- end }}

# Valid channels: analysis, commentary, final. Channel must be included for every message.{{ if \$hasNonBuiltinTools }}
Calls to these tools must go to the commentary channel: 'functions'.
{{- end -}}<|end|>
{{- if or \$hasNonBuiltinTools .System -}}
<|start|>developer<|message|>{{- if \$hasNonBuiltinTools }}# Tools

## functions
namespace functions {
{{- range .Tools }}
{{- if not (or (eq .Function.Name "browser.search") (eq .Function.Name "browser.open") (eq .Function.Name "browser.find") (eq .Function.Name "python")) }}
{{if .Function.Description }}
// {{ .Function.Description }}
{{- end }}
{{- if and .Function.Parameters.Properties (gt (len .Function.Parameters.Properties) 0) }}
type {{ .Function.Name }} = (_: {
{{- range \$name, \$prop := .Function.Parameters.Properties }}
{{- if \$prop.Description }}
  // {{ \$prop.Description }}
{{- end }}
  {{ \$name }}: {{ if gt (len \$prop.Type) 1 }}{{ range \$i, \$t := \$prop.Type }}{{ if \$i }} | {{ end }}{{ \$t }}{{ end }}{{ else }}{{ index \$prop.Type 0 }}{{ end }},
{{- end }}
}) => any;
{{- else }}
type {{ .Function.Name }} = () => any;
{{- end }}
{{- end }}
{{- end }}
} // namespace functions
{{- end }}
{{- if .System}}

# Instructions
{{ .System }}
{{- end -}}
<|end|>
{{- end -}}
{{- \$lastUserIdx := -1 }}
{{- \$prefillingContent := false }}
{{- \$prefillingThinkingOnly := false }}
{{- range \$i, \$msg := .Messages }}
  {{- \$last := eq (len (slice \$.Messages \$i)) 1 -}}
  {{- if eq \$msg.Role "user" }}
    {{- \$lastUserIdx = \$i }}
  {{- end -}}
  {{- if and \$last (eq \$msg.Role "assistant") (gt (len \$msg.Content) 0) }}
    {{- \$prefillingContent = true }}
  {{- else if and \$last (eq \$msg.Role "assistant") (gt (len \$msg.Thinking) 0) }}
    {{- \$prefillingThinkingOnly = true }}
  {{- end }}
{{- end }}
{{- range \$i, \$msg := .Messages }}
  {{- \$last := eq (len (slice \$.Messages \$i)) 1 -}}
  {{- if (ne \$msg.Role "system") -}}
    {{- if eq \$msg.Role "tool" -}}
      {{- if or (eq \$msg.ToolName "python") (eq \$msg.ToolName "browser.search") (eq \$msg.ToolName "browser.open") (eq \$msg.ToolName "browser.find") -}}
        <|start|>{{ \$msg.ToolName }} to=assistant<|message|>{{ \$msg.Content }}<|end|>
      {{- else -}}
        <|start|>functions.{{ \$msg.ToolName }} to=assistant<|message|>{{ \$msg.Content }}<|end|>
      {{- end -}}
    {{- else if eq \$msg.Role "assistant" -}}
      {{- if and \$msg.Thinking (gt \$i \$lastUserIdx) -}}
      <|start|>assistant<|channel|>analysis<|message|>{{ \$msg.Thinking }}{{- if not \$prefillingThinkingOnly -}}<|end|>{{- end -}}
      {{- end -}}
      {{- if gt (len \$msg.Content) 0 -}}
        <|start|>assistant<|channel|>final<|message|>{{ \$msg.Content }}{{- if not \$prefillingContent -}}<|end|>{{- end -}}
      {{- end -}}
      {{- if gt (len \$msg.ToolCalls) 0 -}}
        {{- range \$j, \$toolCall := \$msg.ToolCalls -}}
          {{- \$isBuiltin := or (eq \$toolCall.Function.Name "python") (eq \$toolCall.Function.Name "browser.search") (eq \$toolCall.Function.Name "browser.open") (eq \$toolCall.Function.Name "browser.find") -}}
          <|start|>assistant<|channel|>analysis to={{ if not \$isBuiltin}}functions.{{end}}{{ \$toolCall.Function.Name }} <|constrain|>json<|message|>{{ \$toolCall.Function.Arguments }}<|call|>
        {{- end -}}
      {{- end -}}
    {{- else if eq \$msg.Role "user" -}}
      <|start|>{{ \$msg.Role }}<|message|>{{ \$msg.Content }}<|end|>
    {{- end }}
  {{- else }}
  {{- end }}
{{- end }}
{{- if not (or \$prefillingContent \$prefillingThinkingOnly) -}}
<|start|>assistant<|channel|>analysis<|message|>
# FIX #2: Changed the final cue to force the 'analysis' channel.
{{- end }}"""

PARAMETER num_ctx $CONTEXT_WINDOW
PARAMETER temperature 0.8
EOF

echo "Modelfile ('Modelfile_large') created with context $CONTEXT_WINDOW and cline tool fix."

# --- Build the Model ---
echo "--- Building '$NEW_MODEL_NAME' model... This may take a moment. ---"
ollama create "$NEW_MODEL_NAME" -f ./Modelfile_large
echo "--- Model '$NEW_MODEL_NAME' build complete. ---"

# --- Cleanup ---
rm Modelfile_large
echo "Temporary Modelfile cleaned up."
