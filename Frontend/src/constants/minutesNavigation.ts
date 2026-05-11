/**
 * Shared navigation items for the Minutes Preparation module.
 * 
 * Single source of truth — imported by all minutes sub-pages to ensure
 * consistent sidebar navigation across the module.
 */
import {
  Home,
  FileText,
  Plus,
  FileSpreadsheet,
  History,
  MessageSquare,
  Users,
  BookOpen,
  Eye,
  LucideIcon
} from 'lucide-react';

export interface MinutesNavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  isActive?: boolean;
}

/**
 * Returns the navigation items for the Minutes Preparation module sidebar.
 * Pass the current page id to auto-highlight the active item.
 */
export function getMinutesNavItems(activeId?: string): MinutesNavItem[] {
  const items: MinutesNavItem[] = [
    { id: 'home', label: 'Home', icon: Home, href: '/' },
    { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
    { id: 'create-agenda', label: 'Create Agenda', icon: Plus, href: '/minutes-preparation/create-agenda' },
    { id: 'compliances', label: 'Secretarial Compliances', icon: FileSpreadsheet, href: '/minutes-preparation/compliances' },
    { id: 'ai-mom', label: 'AI MOM', icon: FileText, href: '/minutes-preparation/ai-assistant' },
    { id: 'chatbot', label: 'Meeting Assistant', icon: MessageSquare, href: '/minutes-preparation/chatbot' },
    { id: 'template-resolution', label: 'Template Resolution', icon: History, href: '/minutes-preparation/template-resolution' },
    { id: 'minutes', label: 'Meeting Minutes', icon: FileText, href: '/minutes-preparation/minutes' },
    { id: 'templates', label: 'Templates', icon: FileSpreadsheet, href: '/minutes-preparation/templates' },
    { id: 'renderer', label: 'Template Renderer', icon: Eye, href: '/minutes-preparation/renderer' },
    { id: 'directors', label: 'Directors', icon: Users, href: '/minutes-preparation/directors' },
    { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' },
  ];

  if (activeId) {
    return items.map(item => ({
      ...item,
      isActive: item.id === activeId,
    }));
  }

  return items;
}
