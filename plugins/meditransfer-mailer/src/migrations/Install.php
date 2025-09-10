<?php

namespace pompom\craftmeditransfermailer\migrations;

use Craft;
use craft\db\Migration;

class Install extends Migration
{
    public function safeUp(): bool
    {
        $this->createTables();
        $this->createIndexes();
        $this->addForeignKeys();
        
        return true;
    }
    
    public function safeDown(): bool
    {
        $this->dropForeignKeys();
        $this->dropTables();
        
        return true;
    }
    
    protected function createTables(): void
    {
        // Campaigns table
        $this->createTable('{{%meditransfer_campaigns}}', [
            'id' => $this->primaryKey(),
            'name' => $this->string()->notNull(),
            'subject' => $this->string()->notNull(),
            'templateId' => $this->integer(),
            'fromEmail' => $this->string(),
            'fromName' => $this->string(),
            'replyToEmail' => $this->string(),
            'status' => $this->enum('status', ['draft', 'scheduled', 'sending', 'completed', 'failed'])->defaultValue('draft'),
            'scheduledDate' => $this->dateTime(),
            'completedDate' => $this->dateTime(),
            'sentCount' => $this->integer()->defaultValue(0),
            'totalRecipients' => $this->integer()->defaultValue(0),
            'openedCount' => $this->integer()->defaultValue(0),
            'clickedCount' => $this->integer()->defaultValue(0),
            'bouncedCount' => $this->integer()->defaultValue(0),
            'settings' => $this->text(),
            'dateCreated' => $this->dateTime()->notNull(),
            'dateUpdated' => $this->dateTime()->notNull(),
            'uid' => $this->uid(),
        ]);
        
        // Email templates table
        $this->createTable('{{%meditransfer_templates}}', [
            'id' => $this->primaryKey(),
            'name' => $this->string()->notNull(),
            'handle' => $this->string()->notNull(),
            'subject' => $this->string()->notNull(),
            'htmlContent' => $this->mediumText(),
            'textContent' => $this->text(),
            'variables' => $this->text(),
            'preheaderText' => $this->string(),
            'isActive' => $this->boolean()->defaultValue(true),
            'dateCreated' => $this->dateTime()->notNull(),
            'dateUpdated' => $this->dateTime()->notNull(),
            'uid' => $this->uid(),
        ]);
        
        // Recipients table
        $this->createTable('{{%meditransfer_recipients}}', [
            'id' => $this->primaryKey(),
            'campaignId' => $this->integer()->notNull(),
            'elementId' => $this->integer(),
            'email' => $this->string()->notNull(),
            'name' => $this->string(),
            'organizationName' => $this->string(),
            'organizationType' => $this->string(),
            'customData' => $this->text(),
            'status' => $this->enum('status', ['pending', 'queued', 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed'])->defaultValue('pending'),
            'postmarkMessageId' => $this->string(),
            'sentDate' => $this->dateTime(),
            'openedDate' => $this->dateTime(),
            'clickedDate' => $this->dateTime(),
            'bouncedDate' => $this->dateTime(),
            'errorMessage' => $this->text(),
            'dateCreated' => $this->dateTime()->notNull(),
            'dateUpdated' => $this->dateTime()->notNull(),
            'uid' => $this->uid(),
        ]);
        
        // Email tracking events table
        $this->createTable('{{%meditransfer_tracking}}', [
            'id' => $this->primaryKey(),
            'campaignId' => $this->integer()->notNull(),
            'recipientId' => $this->integer()->notNull(),
            'messageId' => $this->string(),
            'event' => $this->string()->notNull(),
            'eventData' => $this->text(),
            'ipAddress' => $this->string(),
            'userAgent' => $this->text(),
            'clickedUrl' => $this->text(),
            'timestamp' => $this->dateTime()->notNull(),
            'dateCreated' => $this->dateTime()->notNull(),
            'uid' => $this->uid(),
        ]);
        
        // Campaign segments table (for targeting specific entry types)
        $this->createTable('{{%meditransfer_campaign_segments}}', [
            'id' => $this->primaryKey(),
            'campaignId' => $this->integer()->notNull(),
            'sectionId' => $this->integer(),
            'entryTypeId' => $this->integer(),
            'fieldConditions' => $this->text(),
            'dateCreated' => $this->dateTime()->notNull(),
            'dateUpdated' => $this->dateTime()->notNull(),
            'uid' => $this->uid(),
        ]);
    }
    
    protected function createIndexes(): void
    {
        $this->createIndex(null, '{{%meditransfer_campaigns}}', 'status');
        $this->createIndex(null, '{{%meditransfer_campaigns}}', 'scheduledDate');
        $this->createIndex(null, '{{%meditransfer_templates}}', 'handle', true);
        $this->createIndex(null, '{{%meditransfer_recipients}}', ['campaignId', 'email']);
        $this->createIndex(null, '{{%meditransfer_recipients}}', 'status');
        $this->createIndex(null, '{{%meditransfer_recipients}}', 'elementId');
        $this->createIndex(null, '{{%meditransfer_tracking}}', ['campaignId', 'recipientId']);
        $this->createIndex(null, '{{%meditransfer_tracking}}', 'messageId');
        $this->createIndex(null, '{{%meditransfer_tracking}}', 'event');
    }
    
    protected function addForeignKeys(): void
    {
        $this->addForeignKey(null, '{{%meditransfer_recipients}}', 'campaignId', '{{%meditransfer_campaigns}}', 'id', 'CASCADE');
        $this->addForeignKey(null, '{{%meditransfer_recipients}}', 'elementId', '{{%elements}}', 'id', 'SET NULL');
        $this->addForeignKey(null, '{{%meditransfer_tracking}}', 'campaignId', '{{%meditransfer_campaigns}}', 'id', 'CASCADE');
        $this->addForeignKey(null, '{{%meditransfer_tracking}}', 'recipientId', '{{%meditransfer_recipients}}', 'id', 'CASCADE');
        $this->addForeignKey(null, '{{%meditransfer_campaign_segments}}', 'campaignId', '{{%meditransfer_campaigns}}', 'id', 'CASCADE');
        $this->addForeignKey(null, '{{%meditransfer_campaigns}}', 'templateId', '{{%meditransfer_templates}}', 'id', 'SET NULL');
    }
    
    protected function dropForeignKeys(): void
    {
        if ($this->db->tableExists('{{%meditransfer_tracking}}')) {
            $this->dropForeignKey($this->db->getForeignKeyName('{{%meditransfer_tracking}}', 'campaignId'), '{{%meditransfer_tracking}}');
            $this->dropForeignKey($this->db->getForeignKeyName('{{%meditransfer_tracking}}', 'recipientId'), '{{%meditransfer_tracking}}');
        }
        
        if ($this->db->tableExists('{{%meditransfer_recipients}}')) {
            $this->dropForeignKey($this->db->getForeignKeyName('{{%meditransfer_recipients}}', 'campaignId'), '{{%meditransfer_recipients}}');
            $this->dropForeignKey($this->db->getForeignKeyName('{{%meditransfer_recipients}}', 'elementId'), '{{%meditransfer_recipients}}');
        }
        
        if ($this->db->tableExists('{{%meditransfer_campaign_segments}}')) {
            $this->dropForeignKey($this->db->getForeignKeyName('{{%meditransfer_campaign_segments}}', 'campaignId'), '{{%meditransfer_campaign_segments}}');
        }
        
        if ($this->db->tableExists('{{%meditransfer_campaigns}}')) {
            $this->dropForeignKey($this->db->getForeignKeyName('{{%meditransfer_campaigns}}', 'templateId'), '{{%meditransfer_campaigns}}');
        }
    }
    
    protected function dropTables(): void
    {
        $this->dropTableIfExists('{{%meditransfer_tracking}}');
        $this->dropTableIfExists('{{%meditransfer_campaign_segments}}');
        $this->dropTableIfExists('{{%meditransfer_recipients}}');
        $this->dropTableIfExists('{{%meditransfer_campaigns}}');
        $this->dropTableIfExists('{{%meditransfer_templates}}');
    }
}