<?php

namespace pompom\craftmeditransfermailer\services;

use Craft;
use craft\base\Component;
use craft\helpers\Json;
use pompom\craftmeditransfermailer\models\EmailTemplate;
use pompom\craftmeditransfermailer\records\EmailTemplateRecord;

class TemplateService extends Component
{
    public function getAllTemplates(): array
    {
        $records = EmailTemplateRecord::find()
            ->orderBy(['dateCreated' => SORT_DESC])
            ->all();
        
        $templates = [];
        foreach ($records as $record) {
            $templates[] = $this->_createTemplateFromRecord($record);
        }
        
        return $templates;
    }
    
    public function getActiveTemplates(): array
    {
        $records = EmailTemplateRecord::find()
            ->where(['isActive' => true])
            ->orderBy(['name' => SORT_ASC])
            ->all();
        
        $templates = [];
        foreach ($records as $record) {
            $templates[] = $this->_createTemplateFromRecord($record);
        }
        
        return $templates;
    }
    
    public function getTemplateById(int $id): ?EmailTemplate
    {
        $record = EmailTemplateRecord::findOne($id);
        
        if (!$record) {
            return null;
        }
        
        return $this->_createTemplateFromRecord($record);
    }
    
    public function getTemplateByHandle(string $handle): ?EmailTemplate
    {
        $record = EmailTemplateRecord::find()
            ->where(['handle' => $handle])
            ->one();
        
        if (!$record) {
            return null;
        }
        
        return $this->_createTemplateFromRecord($record);
    }
    
    public function saveTemplate(EmailTemplate $template): bool
    {
        $isNew = !$template->id;
        
        if (!$template->validate()) {
            return false;
        }
        
        // Check for unique handle
        $existingRecord = EmailTemplateRecord::find()
            ->where(['handle' => $template->handle])
            ->andWhere($isNew ? [] : ['not', ['id' => $template->id]])
            ->one();
        
        if ($existingRecord) {
            $template->addError('handle', 'Handle wird bereits verwendet');
            return false;
        }
        
        $transaction = Craft::$app->getDb()->beginTransaction();
        
        try {
            if ($isNew) {
                $record = new EmailTemplateRecord();
            } else {
                $record = EmailTemplateRecord::findOne($template->id);
                if (!$record) {
                    throw new \Exception('Template not found');
                }
            }
            
            $record->name = $template->name;
            $record->handle = $template->handle;
            $record->subject = $template->subject;
            $record->htmlContent = $template->htmlContent;
            $record->textContent = $template->textContent;
            $record->variables = Json::encode($template->variables);
            $record->preheaderText = $template->preheaderText;
            $record->isActive = $template->isActive;
            
            if (!$record->save()) {
                throw new \Exception('Could not save template record');
            }
            
            $template->id = $record->id;
            $template->uid = $record->uid;
            
            $transaction->commit();
            
            return true;
            
        } catch (\Exception $e) {
            $transaction->rollBack();
            Craft::error('Failed to save template: ' . $e->getMessage(), __METHOD__);
            return false;
        }
    }
    
    public function deleteTemplate(int $id): bool
    {
        $record = EmailTemplateRecord::findOne($id);
        return $record && $record->delete();
    }
    
    public function createDefaultTemplates(): void
    {
        // Create default MediTransfer template
        $template = new EmailTemplate();
        $template->name = 'MediTransfer Standardvorlage';
        $template->handle = 'meditransfer-default';
        $template->subject = 'Wichtige Information zu MediTransfer';
        $template->preheaderText = 'Erfahren Sie mehr über unseren Patiententransfer-Service';
        
        $template->htmlContent = $this->_getDefaultHtmlTemplate();
        $template->textContent = $this->_getDefaultTextTemplate();
        
        $template->variables = [
            'companyName' => 'Name der Klinik/des Krankenhauses',
            'contactPerson' => 'Ansprechpartner',
            'phone' => 'Telefonnummer',
        ];
        
        $this->saveTemplate($template);
    }
    
    private function _createTemplateFromRecord(EmailTemplateRecord $record): EmailTemplate
    {
        $template = new EmailTemplate();
        $template->id = $record->id;
        $template->uid = $record->uid;
        $template->name = $record->name;
        $template->handle = $record->handle;
        $template->subject = $record->subject;
        $template->htmlContent = $record->htmlContent ?? '';
        $template->textContent = $record->textContent ?? '';
        $template->variables = $record->variables ? Json::decode($record->variables) : [];
        $template->preheaderText = $record->preheaderText ?? '';
        $template->isActive = $record->isActive;
        $template->dateCreated = new \DateTime($record->dateCreated);
        $template->dateUpdated = new \DateTime($record->dateUpdated);
        
        return $template;
    }
    
    private function _getDefaultHtmlTemplate(): string
    {
        return '<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2c5aa0; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background-color: #f9f9f9; }
        .footer { background-color: #333; color: white; padding: 20px; text-align: center; font-size: 12px; }
        .button { display: inline-block; background-color: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0; }
        .button:hover { background-color: #1e3d6f; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MediTransfer</h1>
            <p>Ihr Partner für sichere Patiententransfers</p>
        </div>
        
        <div class="content">
            <h2>Hallo {{recipientName}},</h2>
            
            <p>wir möchten Ihnen MediTransfer vorstellen - die innovative SaaS-Lösung für sichere und effiziente Patiententransfers zwischen medizinischen Einrichtungen.</p>
            
            <h3>Warum MediTransfer?</h3>
            <ul>
                <li>✓ Sichere und verschlüsselte Datenübertragung</li>
                <li>✓ Nahtlose Integration in bestehende Systeme</li>
                <li>✓ Compliance mit allen Datenschutzbestimmungen</li>
                <li>✓ 24/7 Support und Überwachung</li>
            </ul>
            
            <p>Als {{organizationType}} können Sie besonders von unseren spezialisierten Features profitieren.</p>
            
            <a href="https://meditransfer.de/demo" class="button">Kostenlose Demo anfordern</a>
            
            <p>Bei Fragen stehen wir Ihnen gerne zur Verfügung.</p>
            
            <p>Mit freundlichen Grüßen,<br>
            Ihr MediTransfer Team</p>
        </div>
        
        <div class="footer">
            <p>MediTransfer | info@meditransfer.de | Tel: +49 (0) 123 456789</p>
            <p><a href="{{unsubscribeUrl}}" style="color: #ccc;">Abmelden</a></p>
        </div>
    </div>
</body>
</html>';
    }
    
    private function _getDefaultTextTemplate(): string
    {
        return 'Hallo {{recipientName}},

wir möchten Ihnen MediTransfer vorstellen - die innovative SaaS-Lösung für sichere und effiziente Patiententransfers zwischen medizinischen Einrichtungen.

Warum MediTransfer?
- Sichere und verschlüsselte Datenübertragung  
- Nahtlose Integration in bestehende Systeme
- Compliance mit allen Datenschutzbestimmungen
- 24/7 Support und Überwachung

Als {{organizationType}} können Sie besonders von unseren spezialisierten Features profitieren.

Kostenlose Demo anfordern: https://meditransfer.de/demo

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen,
Ihr MediTransfer Team

---
MediTransfer | info@meditransfer.de | Tel: +49 (0) 123 456789
Abmelden: {{unsubscribeUrl}}';
    }
}