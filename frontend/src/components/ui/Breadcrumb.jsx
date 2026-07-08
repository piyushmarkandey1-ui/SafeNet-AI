/**
 * SafeNet AI — Breadcrumb Component
 * 
 * Shows current page context and navigation hierarchy
 */
import { ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './Breadcrumb.css';

export function Breadcrumb({ items }) {
  const navigate = useNavigate();

  if (!items || items.length === 0) return null;

  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <ol className="breadcrumb__list">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          
          return (
            <li key={index} className="breadcrumb__item">
              {isLast ? (
                <span className="breadcrumb__current" aria-current="page">
                  {item.icon && <item.icon size={14} className="breadcrumb__icon" />}
                  {item.label}
                </span>
              ) : (
                <>
                  <button
                    className="breadcrumb__link"
                    onClick={() => item.path && navigate(item.path)}
                    disabled={!item.path}
                  >
                    {item.icon && <item.icon size={14} className="breadcrumb__icon" />}
                    {item.label}
                  </button>
                  <ChevronRight size={14} className="breadcrumb__separator" />
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
