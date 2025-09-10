<?php

namespace pompom\craftmeditransfermailer\models;

use Craft;
use craft\base\Model;
use craft\helpers\DateTimeHelper;
use DateTime;

class Campaign extends Model
{
    public ?int $id = null;
    public ?string $uid = null;
    public string $name = '';
    public string $subject = '';
    public ?int $templateId = null;
    public ?string $fromEmail = null;
    public ?string $fromName = null;
    public ?string $replyToEmail = null;
    public string $status = 'draft';
    public ?DateTime $scheduledDate = null;
    public ?DateTime $completedDate = null;
    public int $sentCount = 0;
    public int $totalRecipients = 0;
    public int $openedCount = 0;
    public int $clickedCount = 0;
    public int $bouncedCount = 0;
    public array $settings = [];
    public ?DateTime $dateCreated = null;
    public ?DateTime $dateUpdated = null;
    
    // Relations
    public ?EmailTemplate $template = null;
    public array $recipients = [];
    public array $segments = [];
    
    public function defineRules(): array
    {
        return [
            [['name', 'subject'], 'required'],
            [['name', 'subject'], 'string', 'max' => 255],
            [['fromEmail', 'replyToEmail'], 'email'],
            [['status'], 'in', 'range' => ['draft', 'scheduled', 'sending', 'completed', 'failed']],
            [['templateId', 'sentCount', 'totalRecipients', 'openedCount', 'clickedCount', 'bouncedCount'], 'integer'],
            [['scheduledDate', 'completedDate'], 'datetime'],
            [['settings'], 'safe'],
        ];
    }
    
    public function attributeLabels(): array
    {
        return [
            'name' => 'Kampagnenname',
            'subject' => 'E-Mail Betreff',
            'templateId' => 'E-Mail Vorlage',
            'fromEmail' => 'Absender E-Mail',
            'fromName' => 'Absender Name',
            'replyToEmail' => 'Antwort E-Mail',
            'status' => 'Status',
            'scheduledDate' => 'Geplantes Versanddatum',
            'totalRecipients' => 'Anzahl Empfänger',
        ];
    }
    
    public function getStatusLabel(): string
    {
        return match($this->status) {
            'draft' => 'Entwurf',
            'scheduled' => 'Geplant',
            'sending' => 'Wird versendet',
            'completed' => 'Abgeschlossen',
            'failed' => 'Fehlgeschlagen',
            default => $this->status,
        };
    }
    
    public function getOpenRate(): float
    {
        if ($this->sentCount === 0) {
            return 0;
        }
        return round(($this->openedCount / $this->sentCount) * 100, 2);
    }
    
    public function getClickRate(): float
    {
        if ($this->sentCount === 0) {
            return 0;
        }
        return round(($this->clickedCount / $this->sentCount) * 100, 2);
    }
    
    public function getBounceRate(): float
    {
        if ($this->sentCount === 0) {
            return 0;
        }
        return round(($this->bouncedCount / $this->sentCount) * 100, 2);
    }
    
    public function canEdit(): bool
    {
        return in_array($this->status, ['draft', 'scheduled']);
    }
    
    public function canSend(): bool
    {
        return $this->status === 'draft' && $this->totalRecipients > 0;
    }
    
    public function canCancel(): bool
    {
        return in_array($this->status, ['scheduled', 'sending']);
    }
    
    public function canDelete(): bool
    {
        return $this->status === 'draft';
    }
}