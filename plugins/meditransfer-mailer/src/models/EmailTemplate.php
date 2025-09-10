<?php

namespace pompom\craftmeditransfermailer\models;

use Craft;
use craft\base\Model;
use DateTime;

class EmailTemplate extends Model
{
    public ?int $id = null;
    public ?string $uid = null;
    public string $name = '';
    public string $handle = '';
    public string $subject = '';
    public string $htmlContent = '';
    public string $textContent = '';
    public array $variables = [];
    public string $preheaderText = '';
    public bool $isActive = true;
    public ?DateTime $dateCreated = null;
    public ?DateTime $dateUpdated = null;
    
    public function defineRules(): array
    {
        return [
            [['name', 'handle', 'subject'], 'required'],
            [['name', 'handle', 'subject', 'preheaderText'], 'string', 'max' => 255],
            [['handle'], 'match', 'pattern' => '/^[a-z][a-zA-Z0-9_]*$/'],
            [['htmlContent', 'textContent'], 'string'],
            [['variables'], 'safe'],
            [['isActive'], 'boolean'],
        ];
    }
    
    public function attributeLabels(): array
    {
        return [
            'name' => 'Vorlagenname',
            'handle' => 'Handle',
            'subject' => 'Betreff',
            'htmlContent' => 'HTML Inhalt',
            'textContent' => 'Text Inhalt',
            'preheaderText' => 'Preheader Text',
            'isActive' => 'Aktiv',
        ];
    }
    
    public function getAvailableVariables(): array
    {
        return array_merge([
            'recipientName' => 'Name des Empfängers',
            'recipientEmail' => 'E-Mail des Empfängers',
            'organizationName' => 'Name der Organisation',
            'organizationType' => 'Art der Organisation',
            'currentDate' => 'Aktuelles Datum',
            'currentYear' => 'Aktuelles Jahr',
            'unsubscribeUrl' => 'Abmelde-Link',
        ], $this->variables);
    }
    
    public function parseContent(string $content, array $variables = []): string
    {
        foreach ($variables as $key => $value) {
            $content = str_replace('{{' . $key . '}}', $value, $content);
        }
        return $content;
    }
}