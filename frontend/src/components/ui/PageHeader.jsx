/**
 * SafeNet AI — Page Header Component
 * 
 * Provides consistent page headers with title, description, and optional actions
 */
import './PageHeader.css';

export function PageHeader({ 
  icon: Icon, 
  title, 
  description, 
  badge,
  actions,
  className = ''
}) {
  return (
    <header className={`page-header ${className}`}>
      <div className="page-header__content">
        <div className="page-header__title-row">
          {Icon && <Icon size={28} className="page-header__icon" />}
          <h1 className="page-header__title">{title}</h1>
          {badge && <span className="page-header__badge">{badge}</span>}
        </div>
        {description && (
          <p className="page-header__description">{description}</p>
        )}
      </div>
      {actions && (
        <div className="page-header__actions">
          {actions}
        </div>
      )}
    </header>
  );
}
